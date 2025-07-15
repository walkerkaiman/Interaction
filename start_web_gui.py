#!/usr/bin/env python3
"""
Simple startup script for the Interactive Art Installation Web GUI
This script is now just a wrapper around main.py --web
"""

import sys
import subprocess
from pathlib import Path

def main():
    print("🚀 Starting Interactive Art Installation Web GUI...")
    print("📝 This script now uses main.py --web which handles everything automatically!")
    
    # Get the directory of this script
    script_dir = Path(__file__).parent.absolute()
    
    try:
        # Start the backend process using main.py
        backend_process = subprocess.Popen([
            sys.executable, "main.py", "--web"
        ], cwd=script_dir)
        
        print("✅ Backend started! The web interface should open automatically in your browser.")
        print("🛑 Press Ctrl+C to stop the server")
        
        # Keep the script running
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping backend server...")
            backend_process.terminate()
            backend_process.wait()
            print("✅ Backend server stopped")
            
    except Exception as e:
        print(f"❌ Error starting backend: {e}")
        return

if __name__ == "__main__":
    main() 