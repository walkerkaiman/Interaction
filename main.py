import os
import sys
import socket
import tkinter as tk
from gui import launch_gui

def is_port_in_use(port):
    """Check if a port is in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True

def create_lock_file():
    """Create a lock file to indicate the app is running"""
    lock_file = "interaction_app.lock"
    try:
        # Try to create the lock file
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return lock_file
    except Exception:
        return None

def remove_lock_file(lock_file):
    """Remove the lock file"""
    try:
        if lock_file and os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass

def check_singleton():
    """Check if another instance is already running"""
    lock_file = "interaction_app.lock"
    
    # Check if lock file exists
    if os.path.exists(lock_file):
        try:
            # Try to read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # Check if the process is still running
                    try:
                        os.kill(pid, 0)  # This will raise an exception if process doesn't exist
                        print(f"❌ Another instance of Interaction App is already running (PID: {pid})")
                        print("Please close the existing instance before starting a new one.")
                        return False
                    except OSError:
                        # Process doesn't exist, remove stale lock file
                        print("🔄 Removing stale lock file from previous instance")
                        remove_lock_file(lock_file)
        except Exception:
            # Lock file is corrupted, remove it
            print("🔄 Removing corrupted lock file")
            remove_lock_file(lock_file)
    
    return True

def main():
    """Main entry point with singleton check"""
    print("🚀 Starting Interaction App...")
    
    # Check if another instance is running
    if not check_singleton():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Create lock file
    lock_file = create_lock_file()
    if not lock_file:
        print("❌ Failed to create lock file. Another instance might be running.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    try:
        print("✅ Starting GUI...")
        launch_gui()
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"💥 Application error: {e}")
    finally:
        # Clean up lock file
        remove_lock_file(lock_file)
        print("👋 Interaction App closed")

if __name__ == "__main__":
    main()