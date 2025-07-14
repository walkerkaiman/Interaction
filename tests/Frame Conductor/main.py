#!/usr/bin/env python3
"""
Frame Conductor - Main Entry Point

A standalone application for sending sACN frame numbers to Universe 999.
This application can be run independently of the Interaction framework.

Usage:
    python main.py
"""

import tkinter as tk
from gui import FrameConductorGUI


def main():
    """Main function to run the Frame Conductor application."""
    # Create the root window
    root = tk.Tk()
    
    # Create the main application
    app = FrameConductorGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start the GUI
    root.mainloop()


if __name__ == "__main__":
    main() 