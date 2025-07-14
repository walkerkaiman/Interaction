#!/usr/bin/env python3
"""
sACN Sender Module for Frame Conductor

Handles sACN communication for sending frame numbers to Universe 999.
Frame numbers are encoded using 2 DMX channels:
- Channel 1: MSB (most significant byte)
- Channel 2: LSB (least significant byte)
- Full frame number: (MSB << 8) | LSB (0-65535)
"""

import threading
import time
from typing import Optional, Callable

# Try to import sacn library
try:
    import sacn
    SACN_AVAILABLE = True
except ImportError:
    SACN_AVAILABLE = False
    print("Warning: sACN library not available. Install with: pip install sacn")


class SACNSender:
    """Handles sACN communication for sending frame numbers."""
    
    def __init__(self, universe: int = 999):
        """
        Initialize the sACN sender.
        
        Args:
            universe (int): sACN universe to send to (default: 999)
        """
        self.universe = universe
        self.sender = None
        self.is_running = False
        self.is_paused = False
        self.current_frame = 0
        self.target_frame = 0
        self.frame_rate = 30
        self.sender_thread = None
        self.frame_callback: Optional[Callable[[int], None]] = None
        
    def set_frame_callback(self, callback: Callable[[int], None]):
        """
        Set callback function to be called when frame is sent.
        
        Args:
            callback (Callable[[int], None]): Function called with current frame number
        """
        self.frame_callback = callback
    
    def initialize_sender(self) -> bool:
        """
        Initialize the sACN sender.
        
        Returns:
            bool: True if initialization was successful, False otherwise
        """
        if not SACN_AVAILABLE:
            return False
            
        try:
            self.sender = sacn.sACNsender()
            self.sender.start()
            self.sender.activate_output(1)  # Activate output 1
            return True
            
        except Exception as e:
            print(f"Error initializing sACN sender: {e}")
            return False
    
    def start_sending(self, target_frame: int, frame_rate: int) -> bool:
        """
        Start sending sACN frames.
        
        Args:
            target_frame (int): Target frame number to send to
            frame_rate (int): Frame rate in fps
            
        Returns:
            bool: True if starting was successful, False otherwise
        """
        if not self.initialize_sender():
            return False
            
        self.target_frame = target_frame
        self.frame_rate = frame_rate
        self.current_frame = 0
        self.is_running = True
        self.is_paused = False
        
        # Start sender thread
        self.sender_thread = threading.Thread(target=self._sender_loop, daemon=True)
        self.sender_thread.start()
        
        return True
    
    def pause_sending(self):
        """Pause or resume sending sACN frames."""
        self.is_paused = not self.is_paused
    
    def stop_sending(self):
        """Stop sending sACN frames and clean up resources."""
        self.is_running = False
        self.is_paused = False
        self.current_frame = 0
        
        # Stop sACN sender
        if self.sender:
            try:
                self.sender.stop()
                self.sender = None
            except Exception as e:
                print(f"Error stopping sACN sender: {e}")
        
        # Wait for thread to finish
        if self.sender_thread and self.sender_thread.is_alive():
            self.sender_thread.join(timeout=1.0)
    
    def get_current_frame(self) -> int:
        """
        Get the current frame number.
        
        Returns:
            int: Current frame number
        """
        return self.current_frame
    
    def get_status(self) -> str:
        """
        Get the current status.
        
        Returns:
            str: Status string ("Running", "Paused", "Stopped")
        """
        if not self.is_running:
            return "Stopped"
        elif self.is_paused:
            return "Paused"
        else:
            return "Running"
    
    def _sender_loop(self):
        """Main loop for sending sACN frames."""
        frame_interval = 1.0 / self.frame_rate
        
        while self.is_running and self.current_frame <= self.target_frame:
            if not self.is_paused:
                try:
                    # Encode frame number into DMX channels 1 and 2
                    msb = (self.current_frame >> 8) & 0xFF  # Most significant byte
                    lsb = self.current_frame & 0xFF         # Least significant byte
                    
                    # Create DMX data (512 channels, all zeros except channels 1 and 2)
                    dmx_data = [0] * 512
                    dmx_data[0] = msb  # Channel 1 (0-indexed)
                    dmx_data[1] = lsb  # Channel 2 (0-indexed)
                    
                    # Send sACN data to Universe 999
                    dmx_tuple = tuple(dmx_data)
                    self.sender[1].dmx_data = dmx_tuple  # type: ignore
                    
                    # Set universe (this might be handled differently in some versions)
                    try:
                        self.sender[1].universe = self.universe  # type: ignore
                    except:
                        pass  # Universe might be set differently
                    
                    # Call frame callback if set
                    if self.frame_callback:
                        self.frame_callback(self.current_frame)
                    
                    # Increment frame
                    self.current_frame += 1
                    
                    # Sleep for frame interval
                    time.sleep(frame_interval)
                    
                except Exception as e:
                    print(f"Error sending frame {self.current_frame}: {e}")
                    time.sleep(0.1)
            else:
                time.sleep(0.1)
    
    def is_sacn_available(self) -> bool:
        """
        Check if sACN library is available.
        
        Returns:
            bool: True if sACN library is available, False otherwise
        """
        return SACN_AVAILABLE 