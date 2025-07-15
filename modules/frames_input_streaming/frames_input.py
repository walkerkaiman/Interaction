"""
sACN Frames Input Streaming Module

This module listens for sACN (Streaming ACN, E1.31) frame numbers on a specific universe
and emits streaming events with the frame number as value.

Streaming Module Contract:
- Streaming input modules must emit events with a 'value' key containing the data to stream.
- Streaming output modules will use the 'value' key from incoming events.
- The 'stream': True key is used for routing/identification but is not required by outputs.

Streaming Event Format:
{
    'value': <the_value>,
    'stream': True,
    ... # (other metadata, not required by outputs)
}

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

class SACNFramesInputStreamingModule(ModuleBase):
    """
    sACN Frames Input Streaming Module
    
    Listens for sACN frame numbers on a specific universe and emits streaming events.
    The frame number is extracted from DMX channels 1 and 2 using MSB/LSB encoding.
    
    Configuration:
    - universe (int): sACN universe to listen to (default: 999)
    
    Streaming Event Data:
    - value (int): Current frame number (0-65535)
    - stream (bool): Always True
    - universe (int): Universe number
    - timestamp (float): Time of event
    """
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], 
                 log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.universe = 999  # Hardcoded to Universe 999
        self.receiver = None
        self.receiver_thread = None
        self.is_running = False
        self.current_frame = 0
        self.last_frame = -1
        self.frame_lock = threading.Lock()
        if not SACN_AVAILABLE:
            self.log_message("❌ sACN library not available. Install with: pip install sacn")
            return
        self.log_message(f"sACN Frames Input Streaming initialized - Universe: {self.universe}")

    def start(self):
        super().start()
        if not SACN_AVAILABLE:
            self.log_message("❌ Cannot start sACN receiver - library not available")
            return
        try:
            self.receiver = sacn.sACNreceiver()
            self.receiver.start()
            self.receiver.on_dmx_data_change = self._dmx_data_callback
            self.receiver.join_multicast(self.universe)
            self.is_running = True
            self.log_message(f"✅ sACN receiver started on Universe {self.universe}")
        except Exception as e:
            self.log_message(f"❌ Failed to start sACN receiver: {e}")

    def stop(self):
        """
        Stop the sACN Frames Input Streaming module and clean up resources.
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
        # Join any custom threads (if used in future)
        if self.receiver_thread and hasattr(self.receiver_thread, 'is_alive'):
            if self.receiver_thread.is_alive():
                self.receiver_thread.join(timeout=2)
            self.receiver_thread = None

    def _dmx_data_callback(self, packet):
        try:
            universe = packet.universe
            dmx_data = packet.dmxData
            frame_number = self._extract_frame_number(dmx_data)
            with self.frame_lock:
                self.current_frame = frame_number
            if frame_number != self.last_frame:
                old_frame = self.last_frame
                self.last_frame = frame_number
                event_data = {
                    'value': frame_number,
                    'stream': True,
                    'universe': universe,
                    'timestamp': time.time()
                }
                self.emit_event(event_data)
                # Only log significant frame changes to reduce console spam
                if frame_number > 0:
                    self.log_message(f"📡 Frame change: {old_frame} -> {frame_number}")
        except Exception as e:
            self.log_message(f"❌ Error in DMX data callback: {e}")

    def _extract_frame_number(self, dmx_data) -> int:
        try:
            msb = dmx_data[0] if len(dmx_data) > 0 else 0
            lsb = dmx_data[1] if len(dmx_data) > 1 else 0
            frame_number = (msb << 8) | lsb
            return frame_number
        except Exception as e:
            self.log_message(f"❌ Error extracting frame number: {e}")
            return 0

    def get_display_data(self) -> Dict[str, Any]:
        with self.frame_lock:
            frame_display = "No frame received" if self.current_frame == 0 else str(self.current_frame)
            return {
                'frame_number': frame_display,
                'connection_status': "Connected" if self.is_running else "Disconnected"
            }

    def update_config(self, new_config: Dict[str, Any]):
        super().update_config(new_config)
        # Universe is hardcoded to 999, no configuration needed

    def get_output_config(self) -> Dict[str, Any]:
        return {
            "universe": self.universe,
            "frame_number": self.current_frame
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "universe": self.universe,
            "current_frame": self.current_frame
        } 

    def set_event_callback(self, callback):
        """
        Set the event callback function for compatibility with GUI and router.
        Args:
            callback: Function to call when events are emitted
        """
        self.add_event_callback(callback) 