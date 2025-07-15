"""
sACN Frames Input Trigger Module

This module listens for sACN (Streaming ACN, E1.31) frame numbers on a specific universe.
The frame number is encoded using 2 DMX channels:
- Channel 1: MSB (most significant byte)
- Channel 2: LSB (least significant byte)
- Full frame number: (MSB << 8) | LSB (0-65535)

The module triggers events when frame numbers change and updates the GUI display.

Author: Interaction Framework Team
License: MIT
"""

import threading
import time
from typing import Dict, Any, Optional
from modules.module_base import ModuleBase

# Try to import sacn library
try:
    import sacn
    SACN_AVAILABLE = True
except ImportError:
    SACN_AVAILABLE = False

class SACNFramesInputModule(ModuleBase):
    """
    sACN Frames Input Trigger Module
    
    This module listens for sACN frame numbers on a specific universe and triggers
    events when frame numbers change. The frame number is extracted from DMX channels
    1 and 2 using MSB/LSB encoding.
    
    Configuration:
    - universe (int): sACN universe to listen to (default: 999)
    
    Event Data:
    - frame_number (int): Current frame number (0-65535)
    - trigger (bool): True when frame number changes
    
    The module runs a non-blocking sACN receiver in a separate thread to handle
    high-frequency frame updates (30fps+) without blocking the main application.
    """
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], 
                 log_callback=print):
        """
        Initialize the sACN frames input module.
        
        Args:
            config (Dict[str, Any]): Module configuration
            manifest (Dict[str, Any]): Module manifest
            log_callback: Function to call for logging
        """
        super().__init__(config, manifest, log_callback)
        
        # Extract configuration values with defaults
        self.universe = 999  # Hardcoded to Universe 999
        
        # sACN receiver state
        self.receiver = None
        self.receiver_thread = None
        self.is_running = False
        
        # Frame tracking
        self.current_frame = 0
        self.last_frame = -1  # Start with -1 to trigger on first frame
        self.frame_lock = threading.Lock()
        
        # Check if sacn library is available
        if not SACN_AVAILABLE:
            self.log_message("❌ sACN library not available. Install with: pip install sacn")
            return
        
        self.log_message(f"sACN Frames Input initialized - Universe: {self.universe}")
    
    def start(self):
        """
        Start the sACN receiver and begin listening for frames.
        
        This method initializes the sACN receiver and starts a background thread
        to handle incoming sACN data without blocking the main application.
        """
        super().start()
        
        if not SACN_AVAILABLE:
            self.log_message("❌ Cannot start sACN receiver - library not available")
            return
        
        try:
            self.log_message("[DEBUG] Creating sACN receiver instance...")
            # Create sACN receiver
            self.receiver = sacn.sACNreceiver()
            self.receiver.start()
            self.log_message("[DEBUG] sACN receiver started.")
            
            # Set callback for DMX data changes using the correct API
            self.log_message("[DEBUG] Setting on_dmx_data_change callback...")
            self.receiver.on_dmx_data_change = self._dmx_data_callback
            
            # Join the universe
            self.log_message(f"[DEBUG] Joining multicast universe {self.universe}...")
            self.receiver.join_multicast(self.universe)
            self.log_message(f"📡 Joined sACN Universe {self.universe}")
            
            # Start receiver thread (kept for potential future use)
            self.is_running = True
            
            self.log_message(f"✅ sACN receiver started on Universe {self.universe}")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start sACN receiver: {e}")
    
    def stop(self):
        """
        Stop the sACN Frames Input Trigger module and clean up resources.
        Ensures all threads and resources are properly released.
        """
        super().stop()
        self.is_running = False
        # Stop sACN receiver if running
        if self.receiver:
            try:
                self.receiver.stop()
                self.log_message(f"🛑 sACN receiver stopped on Universe {self.universe}")
            except Exception as e:
                self.log_message(f"⚠️ Error stopping sACN receiver: {e}")
            self.receiver = None
        # Join any custom threads (if used)
        if self.receiver_thread and hasattr(self.receiver_thread, 'is_alive'):
            if self.receiver_thread.is_alive():
                self.log_message("[DEBUG] Joining receiver_thread...")
                self.receiver_thread.join(timeout=2)
            self.receiver_thread = None
        self.log_message(f"[DEBUG] sacn_frames_input_trigger stop() completed and all references cleaned up")
    
    def _dmx_data_callback(self, packet):
        """
        Callback function for DMX data changes.
        
        Args:
            packet: sACN data packet containing universe and DMX data
        """
        try:
            universe = packet.universe
            dmx_data = packet.dmxData
            
            # Extract frame number from channels 1 and 2
            frame_number = self._extract_frame_number(dmx_data)
            
            # Update current frame
            with self.frame_lock:
                self.current_frame = frame_number
            
            # Check if frame number changed
            if frame_number != self.last_frame:
                self.last_frame = frame_number
                
                # Trigger event
                event_data = {
                    'frame_number': frame_number,
                    'trigger': True,
                    'universe': universe,
                    'timestamp': time.time()
                }
                
                # Emit event to connected modules
                self.emit_event(event_data)
                
                # Log frame change
                self.log_message(f"🎬 Frame: {frame_number} (Universe {universe})")
                
        except Exception as e:
            self.log_message(f"❌ Error in DMX data callback: {e}")
    
    def _extract_frame_number(self, dmx_data) -> int:
        """
        Extract frame number from DMX channels 1 and 2.
        
        Args:
            dmx_data: DMX data from sACN receiver
            
        Returns:
            int: Frame number (0-65535)
        """
        try:
            # Extract MSB (channel 1) and LSB (channel 2)
            # Note: DMX channels are 1-indexed, but array is 0-indexed
            msb = dmx_data[0] if len(dmx_data) > 0 else 0  # Channel 1
            lsb = dmx_data[1] if len(dmx_data) > 1 else 0  # Channel 2
            
            # Calculate frame number: (MSB << 8) | LSB
            frame_number = (msb << 8) | lsb
            
            return frame_number
            
        except Exception as e:
            self.log_message(f"❌ Error extracting frame number: {e}")
            return 0
    
    def get_display_data(self) -> Dict[str, Any]:
        """
        Get current display data for the GUI.
        
        Returns:
            Dict[str, Any]: Display data including current frame number
        """
        with self.frame_lock:
            # Show "No frame received" when no frames have been received yet
            frame_display = "No frame received" if self.current_frame == 0 else str(self.current_frame)
            return {
                'frame_number': frame_display,
                'status': "Connected" if self.is_running else "Disconnected"
            }
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update module configuration.
        
        Args:
            new_config (Dict[str, Any]): New configuration values
        """
        super().update_config(new_config)
        
        # Universe is hardcoded to 999, no configuration needed
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get current configuration for output.
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        return {
            "universe": self.universe,
            "frame_number": self.current_frame
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert module state to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Module state
        """
        return {
            "universe": self.universe,
            "current_frame": self.current_frame
        }
    
    def set_event_callback(self, callback):
        """
        Set the event callback function for compatibility with GUI.
        
        Args:
            callback: Function to call when events are emitted
        """
        self.add_event_callback(callback)
    
    def auto_configure(self):
        """
        Auto-configure the module with sensible defaults.
        """
        if not self.universe:
            self.universe = 999
            self.log_message(f"🔧 Auto-configured universe to {self.universe}") 