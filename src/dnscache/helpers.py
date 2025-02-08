import os


def is_root() -> bool:
    """Check if the script is run as root.

    Returns:
        True if the script is run as root, False otherwise.
    """
    try:
        if os.name == "nt":
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.getuid() == 0
    except Exception:
        return False
