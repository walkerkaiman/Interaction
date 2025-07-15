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
import argparse
import threading
import time
import webbrowser
from pathlib import Path

# Performance optimization imports
from performance import initialize_performance_optimizations, PerformanceLevel, shutdown_performance_manager

# Optionally import Tkinter GUI
try:
    from gui import launch_gui
except ImportError:
    launch_gui = None

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
    print("🚀 Starting Interaction App...")
    # Initialize performance optimizations
    perf_manager = initialize_performance_optimizations(PerformanceLevel.BALANCED)
    parser = argparse.ArgumentParser(description="Interaction App Backend")
    parser.add_argument('--web', action='store_true', help='Start the web backend (default)')
    parser.add_argument('--gui', action='store_true', help='Start the legacy Tkinter GUI')
    args = parser.parse_args()

    if not check_singleton():
        input("Press Enter to exit...")
        sys.exit(1)
    lock_file = create_lock_file()
    if not lock_file:
        print("❌ Failed to create lock file. Another instance might be running.")
        input("Press Enter to exit...")
        sys.exit(1)
    try:
        if args.gui and launch_gui:
            print("✅ Starting legacy GUI...")
            launch_gui()
        else:
            print("✅ Starting web backend...")
            
            # Get the path to the web interface
            web_gui_path = Path(__file__).parent / "web-frontend" / "simple-gui.html"
            
            # Check if the web GUI file exists
            if not web_gui_path.exists():
                print(f"⚠️  Web GUI file not found at: {web_gui_path}")
                print("Starting backend without web interface...")
                import web_backend
                web_backend.run()
            else:
                # Start the web backend in a separate thread
                def start_web_backend():
                    import web_backend
                    web_backend.run()
                
                backend_thread = threading.Thread(target=start_web_backend, daemon=True)
                backend_thread.start()
                
                # Wait a moment for the server to start
                print("⏳ Waiting for server to start...")
                time.sleep(3)
                
                # Open the web interface in the default browser
                print("🌐 Opening web interface...")
                try:
                    webbrowser.open(f"file://{web_gui_path}")
                    print("✅ Web interface opened in browser!")
                    print("🔗 Manual URL: file://" + str(web_gui_path))
                except Exception as e:
                    print(f"⚠️  Could not open browser automatically: {e}")
                    print("🔗 Please manually open: file://" + str(web_gui_path))
                
                print("🛑 Press Ctrl+C to stop the server")
                
                # Keep the main thread running
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping web backend...")
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"💥 Application error: {e}")
    finally:
        remove_lock_file(lock_file)
        shutdown_performance_manager()
        print("👋 Interaction App closed")

if __name__ == "__main__":
    main()