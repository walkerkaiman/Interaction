"""
Interaction - Interactive Art Installation Framework
Main Application Entry Point

This file implements a singleton pattern to ensure only one instance of the
Interaction application can run at a time. This prevents port conflicts,
resource contention, and data corruption that can occur with multiple instances.

The singleton pattern uses a lock file mechanism:
1. Check if a lock file exists
2. If it exists, verify if the process is still running
3. If the process is dead, remove the stale lock file
4. If the process is alive, prevent startup
5. If no lock file exists, create one and start the application
6. Clean up the lock file on exit

Author: Interaction Framework Team
License: MIT
"""

import os
import sys
import socket
import tkinter as tk
from gui import launch_gui

def is_port_in_use(port):
    """
    Check if a specific port is in use by attempting to bind to it.
    
    Args:
        port (int): Port number to check
        
    Returns:
        bool: True if port is in use, False if available
        
    Note: This is a utility function for port availability checking,
    though the main singleton mechanism uses lock files instead.
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
    
    The lock file contains the current process ID (PID) so we can
    verify if the process is still alive later.
    
    Returns:
        str: Path to the created lock file, or None if creation failed
        
    Note: The lock file is created in the current working directory
    and named 'interaction_app.lock'.
    """
    lock_file = "interaction_app.lock"
    try:
        # Write the current process ID to the lock file
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
        
    Note: This function is called during cleanup to ensure the lock file
    is removed even if the application crashes or is forcefully terminated.
    """
    try:
        if lock_file and os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass

def check_singleton():
    """
    Check if another instance of the application is already running.
    
    This function implements the core singleton logic:
    1. Check if the lock file exists
    2. If it exists, read the PID and verify the process is alive
    3. If the process is dead, remove the stale lock file
    4. If the process is alive, prevent startup
    5. If no lock file exists, allow startup
    
    Returns:
        bool: True if no other instance is running, False otherwise
        
    Note: This prevents multiple instances from running simultaneously,
    which would cause port conflicts and resource contention.
    """
    lock_file = "interaction_app.lock"
    
    # Check if lock file exists
    if os.path.exists(lock_file):
        try:
            # Read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # Check if the process is still running
                    try:
                        # os.kill(pid, 0) sends signal 0 (no signal) to check if process exists
                        # This will raise an OSError if the process doesn't exist
                        os.kill(pid, 0)
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
    """
    Main entry point for the Interaction application.
    
    This function:
    1. Checks if another instance is running (singleton check)
    2. Creates a lock file if no other instance is running
    3. Launches the GUI
    4. Ensures cleanup on exit
    
    The application uses a try-finally block to ensure the lock file
    is always removed, even if the application crashes or is interrupted.
    """
    print("🚀 Starting Interaction App...")
    
    # Step 1: Check if another instance is running
    if not check_singleton():
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Step 2: Create lock file to prevent other instances
    lock_file = create_lock_file()
    if not lock_file:
        print("❌ Failed to create lock file. Another instance might be running.")
        input("Press Enter to exit...")
        sys.exit(1)
    
    try:
        # Step 3: Launch the GUI
        print("✅ Starting GUI...")
        launch_gui()
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        # Handle any other exceptions
        print(f"💥 Application error: {e}")
    finally:
        # Step 4: Always clean up the lock file
        remove_lock_file(lock_file)
        print("👋 Interaction App closed")
        
        # Force exit after cleanup to prevent hanging
        import os
        os._exit(0)

if __name__ == "__main__":
    # Only run main() if this file is executed directly
    # This prevents the singleton check from running when the file is imported
    main()