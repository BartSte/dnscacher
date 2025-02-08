import subprocess
from unittest import TestCase
from unittest.mock import MagicMock, patch

from dnscache.ipset import IpSet, IpSetError


class TestIpSet(TestCase):
    def setUp(self):
        """Set up a test IpSet instance."""
        self.ipset_name = "test_ipset"
        self.ipset = IpSet(self.ipset_name)

    @patch("subprocess.check_call")
    def test_make_success(self, mock_check_call):
        """Test that IpSet.make() succeeds when subprocess calls succeed."""
        mock_check_call.return_value = 0
        self.ipset.make()
        self.assertTrue(mock_check_call.called)

    @patch("subprocess.run")
    def test_add_success(self, mock_run):
        """Test that IpSet.add() succeeds when subprocess.run returns returncode
        0."""
        fake_process = MagicMock()
        fake_process.returncode = 0
        mock_run.return_value = fake_process
        ips = {"1.2.3.4", "5.6.7.8"}
        self.ipset.add(ips)
        self.assertTrue(mock_run.called)

    @patch("subprocess.run")
    def test_add_failure(self, mock_run):
        """Test that IpSet.add() raises an IpSetError when adding IPs fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1, ["ipset", "restore"]
        )
        with self.assertRaises(IpSetError):
            self.ipset.add({"1.2.3.4"})

    @patch("subprocess.run")
    def test_block_success(self, mock_run):
        """Test that IpSet.block() succeeds when iptables command returns
        returncode 0."""
        fake_process = MagicMock()
        fake_process.returncode = 0

        mock_run.return_value = fake_process
        self.ipset.block()
        self.assertTrue(mock_run.called)

    @patch("subprocess.run")
    def test_block_failure(self, mock_run):
        """Test that IpSet.block() raises an IpSetError when blocking fails."""
        mock_run.side_effect = subprocess.CalledProcessError(
            1,
            [
                "iptables",
                "-I",
                "INPUT",
                "-m",
                "set",
                "--match-set",
                self.ipset_name,
                "src",
                "-j",
                "DROP",
            ],
        )
        with self.assertRaises(IpSetError):
            self.ipset.block()
