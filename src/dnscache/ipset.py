import logging
import subprocess


class IpSet:
    """A helper class for managing ipset operations.

    Attributes:
        name (str): The name of the ipset.

    """

    name: str

    def __init__(self, name: str):
        """Initialize the IpSet.

        Args:
            name (str): The name of the ipset.

        """
        self.name = name

    def make(self):
        """Create the ipset.

        Raises:
            IpSetError: If creation fails.

        """
        try:
            exitcode: int = subprocess.check_call(
                ["ipset", "create", self.name, "hash:ip"],
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            exitcode = subprocess.check_call(["ipset", "flush", self.name])

        if not exitcode:
            logging.info("Empty ipset '%s' created", self.name)
        else:
            raise IpSetError(
                f"Error creating/flushing ipset {self.name}: the exit code was "
                f"{exitcode}"
            )

    def add(self, ips: set[str]):
        """Add IPs to the ipset.

        Args:
            ips (set[str]): Set of IP addresses to add.

        Raises:
            IpSetError: If adding IPs fails.

        """
        commands: str = "\n".join(f"add {self.name} {ip}" for ip in ips)
        try:
            process = subprocess.run(
                ["ipset", "restore"], input=commands.encode(), check=True
            )
        except subprocess.CalledProcessError as e:
            raise IpSetError(
                f"Error adding IPs to ipset {self.name}: {e.stderr}"
            ) from e

        if not process.returncode:
            logging.info("Added %s IPs to ipset %s", len(ips), self.name)
        else:
            raise IpSetError(
                f"Error adding IPs to ipset {self.name}: the exit code was "
                f"{process.returncode}"
            )

    def block(self):
        """Insert an iptables rule to block packets from IPs in the ipset.

        Raises:
            IpSetError: If blocking fails.

        """
        cmd: str = (
            f"iptables -I INPUT -m set --match-set '{self.name}' src -j DROP"
        )
        try:
            process = subprocess.run(cmd.split(), check=True)
        except subprocess.CalledProcessError as e:
            raise IpSetError(
                f"Error blocking IPs in ipset {self.name}: {e.stderr}"
            ) from e

        if not process.returncode:
            logging.info("Blocked IPs in ipset %s", self.name)
        else:
            raise IpSetError(
                f"Error blocking IPs in ipset {self.name}: the exit code was "
                f"{process.returncode}"
            )

    def block_persistent(self):
        """Same as `block` but persists the rule across reboots."""
        self.block()
        with open("/etc/iptables/iptables.rules", "w") as f:
            subprocess.run(["iptables-save"], stdout=f)
        logging.info("Saved iptables rules to /etc/iptables/iptables.rules")


class IpSetError(Exception):
    """Raised when an error occurs during ipset operations."""
