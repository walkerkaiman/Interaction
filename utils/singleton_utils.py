import os
import socket

def is_port_in_use(port):
    """
    Check if a specific port is in use by attempting to bind to it.
    Args:
        port (int): Port number to check
    Returns:
        bool: True if port is in use, False if available
    Note: This is a utility function for port availability checking.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True

def create_lock_file():
    """
    Create a lock file to indicate the application is running.
    The lock file contains the current process ID (PID).
    Returns:
        str: Path to the created lock file, or None if creation failed
    """
    lock_file = "interaction_app.lock"
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return lock_file
    except Exception:
        return None

def remove_lock_file(lock_file):
    """
    Remove the lock file to indicate the application has stopped.
    Args:
        lock_file (str): Path to the lock file to remove
    """
    try:
        if lock_file and os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass

def check_singleton():
    """
    Check if another instance of the application is already running.
    Returns:
        bool: True if no other instance is running, False otherwise
    """
    lock_file = "interaction_app.lock"
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    try:
                        os.kill(pid, 0)
                        return False
                    except OSError:
                        remove_lock_file(lock_file)
        except Exception:
            remove_lock_file(lock_file)
    return True 