"""
OSC Output Module - Adaptive OSC Message Sender

This module implements a unified OSC output system that can adapt its behavior
based on the type of input module connected to it. It automatically switches
between trigger mode and streaming mode based on the input module's classification.

Key Features:
1. Automatic mode detection based on connected input module
2. Trigger mode: Sends value 1 when triggered (compatible with trigger inputs)
3. Streaming mode: Sends actual data values (compatible with streaming inputs)
4. Dynamic behavior switching without configuration changes
5. Backward compatibility with existing OSC output modules

The module uses the input module's classification to determine behavior:
- Input classification "trigger" → Trigger mode (sends value 1)
- Input classification "streaming" → Streaming mode (sends actual data)

Author: Interaction Framework Team
License: MIT
"""

import socket
import threading
import time
from modules.module_base import ModuleBase
from pythonosc import udp_client

class OSCOutputModule(ModuleBase):
    """
    OSC output module that adapts behavior based on connected input module.
    
    This module automatically detects the classification of the connected input
    module and adjusts its behavior accordingly:
    
    - Trigger Mode: When connected to a trigger input module, sends value 1
    - Streaming Mode: When connected to a streaming input module, sends actual data
    
    The module maintains the same configuration interface as the original OSC
    output modules but provides unified functionality.
    
    Configuration:
    - ip_address (str): Target IP address for OSC messages
    - port (int): Target port for OSC messages  
    - osc_address (str): OSC address pattern to send to
    
    Event Handling:
    The module automatically adapts its event handling based on the input
    module's classification, providing seamless integration with both
    trigger and streaming input modules.
    """
    
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        
        # OSC connection parameters
        self.ip_address = config.get('ip_address', '127.0.0.1')
        self.port = int(config.get('port', 8000))
        self.osc_address = config.get('osc_address', '/data')
        
        # OSC client
        self.osc_client = None
        self._lock = threading.Lock()
        
        # Connection state
        self.connection_status = "Disconnected"
        self.last_sent_data = "No data sent"
        
        # Mode detection
        self.current_mode = "unknown"  # "trigger", "streaming", or "unknown"
        self.connected_input_classification = None
        
        # Initialize OSC client
        self._setup_osc_client()
        
        self.log_message(f"OSC Output initialized - IP: {self.ip_address}, Port: {self.port}, Address: {self.osc_address}")

    def start(self):
        super().start()
        # Subscribe to module_event events with a filter for matching input settings
        def event_filter(event, settings):
            # Match on settings if needed (e.g., OSC address, etc.)
            # For now, accept all events; refine as needed for settings-based routing
            return True
        self.event_router.subscribe('module_event', self.handle_event, event_filter)
        self.log_message(f"OSC Output started and subscribed to events.")

    def stop(self):
        """Stop the unified OSC output module"""
        self._disconnect()
        super().stop()
        self.log_message(f"🛑 Unified OSC output module stopped (instance {self.instance_id})")

    def wait_for_stop(self):
        """
        Wait for any background tasks/threads to finish (future-proof).
        """
        # No background threads currently, but method is here for consistency
        pass

    def update_config(self, config):
        """Update the module configuration"""
        old_ip = self.ip_address
        old_port = self.port
        old_address = self.osc_address
        
        self.ip_address = config.get('ip_address', self.ip_address)
        self.port = int(config.get('port', self.port))
        self.osc_address = config.get('osc_address', self.osc_address)
        
        # If any parameter changed, reconnect
        if old_ip != self.ip_address or old_port != self.port or old_address != self.osc_address:
            self.log_message(f"🔄 OSC config updated - IP: {self.ip_address}, Port: {self.port}, Address: {self.osc_address}")
            self._setup_osc_client()

    def set_input_classification(self, classification):
        """
        Set the classification of the connected input module.
        
        Args:
            classification (str): Input module classification ("trigger" or "streaming")
            
        This method is called by the module loader or GUI to inform the output
        module about the type of input module it's connected to, allowing it
        to adapt its behavior accordingly.
        """
        if classification != self.connected_input_classification:
            self.connected_input_classification = classification
            if classification == "trigger":
                self.current_mode = "trigger"
                self.log_message(f"🔄 Switched to TRIGGER mode (sends value 1)")
            elif classification == "streaming":
                self.current_mode = "streaming"
                self.log_message(f"🔄 Switched to STREAMING mode (sends actual data)")
            else:
                self.current_mode = "unknown"
                self.log_message(f"⚠️ Unknown input classification: {classification}")

    def auto_configure(self):
        """
        If no ip_address, port, or osc_address is set, use sensible defaults.
        """
        if not getattr(self, 'ip_address', None):
            self.ip_address = '127.0.0.1'
            self.config['ip_address'] = '127.0.0.1'
            self.log_message("[Auto-configure] Set default IP address: 127.0.0.1")
        if not getattr(self, 'port', None):
            self.port = 9001
            self.config['port'] = 9001
            self.log_message("[Auto-configure] Set default OSC port: 9001")
        if not getattr(self, 'osc_address', None):
            self.osc_address = '/play'
            self.config['osc_address'] = '/play'
            self.log_message("[Auto-configure] Set default OSC address: /play")

    def _setup_osc_client(self):
        """Setup the OSC client connection"""
        try:
            self._disconnect()  # Close any existing connection
            
            # Create new OSC client
            self.osc_client = udp_client.SimpleUDPClient(self.ip_address, self.port)
            
            # Test the connection by sending a ping message
            try:
                self.osc_client.send_message("/ping", "test")
                self.connection_status = "Connected"
                self.log_message(f"✅ Connected to {self.ip_address}:{self.port}")
            except Exception as e:
                self.connection_status = f"Warning: {str(e)}"
                self.log_message(f"⚠️ OSC client created but connection test failed: {e}")
                
        except Exception as e:
            self.connection_status = f"Error: {str(e)}"
            self.log_message(f"❌ Failed to setup OSC client: {e}")
            self.osc_client = None

    def _disconnect(self):
        """Close OSC connection"""
        if self.osc_client:
            try:
                # Note: pythonosc doesn't have an explicit close method
                # The client will be garbage collected
                self.osc_client = None
                self.log_message(f"🔌 Disconnected from {self.ip_address}:{self.port}")
            except Exception as e:
                self.log_message(f"⚠️ Error closing OSC connection: {e}")
        
        self.connection_status = "Disconnected"

    def _parse_value(self, data):
        """
        Parse incoming data and convert to appropriate type.
        Returns (value, type_name) tuple.
        """
        try:
            # Extract value from event data
            if isinstance(data, dict):
                value = data.get('value', str(data))
            else:
                value = str(data)
            # Only call .strip() if value is a string
            if isinstance(value, str):
                value = value.strip()
            else:
                # If not a string, leave as is (int, float, etc.)
                pass
            if value == '' or value is None:
                return None, "empty"
            # Check if it's a float (contains decimal point and is string)
            if isinstance(value, str) and '.' in value:
                try:
                    float_val = float(value)
                    return float_val, "float"
                except ValueError:
                    return value, "string"
            # Check if it's an integer (if string or already int)
            if isinstance(value, str):
                try:
                    int_val = int(value)
                    return int_val, "integer"
                except ValueError:
                    return value, "string"
            elif isinstance(value, int):
                return value, "integer"
            elif isinstance(value, float):
                return value, "float"
            else:
                return value, type(value).__name__  # fallback
        except Exception as e:
            self.log_message(f"⚠️ Error parsing value '{data}': {e}")
            return str(data), "string"

    def handle_event(self, event, settings=None):
        if self.strategy:
            self.strategy.process_event(event)
        else:
            data = event['data'] if isinstance(event, dict) and 'data' in event else event
            
            try:
                # Determine behavior based on current mode
                if self.current_mode == "trigger":
                    # Trigger mode: Only respond to trigger events and send value 1
                    if not data.get('trigger', False):
                        return
                    
                    # Update last sent data for display
                    with self._lock:
                        self.last_sent_data = f"1 (trigger mode)"
                    
                    # Send OSC message with value 1
                    if self.osc_client:
                        try:
                            self.osc_client.send_message(self.osc_address, 1)
                            self.log_message(f"OSC Sent (trigger): {self.osc_address} = 1")
                            # Use the proper logging callback for OSC messages
                            if hasattr(self, 'log_callback') and self.log_callback:
                                self.log_callback(f"OSC SENT: {self.osc_address} = 1 (trigger) to {self.ip_address}:{self.port}")
                        except Exception as e:
                            self.log_message(f"❌ Failed to send OSC message: {e}")
                            self.connection_status = f"Send Error: {str(e)}"
                            # Try to reconnect
                            self._setup_osc_client()
                    else:
                        self.log_message(f"⚠️ OSC client not available, cannot send: 1 (trigger)")
                
                elif self.current_mode == "streaming":
                    # Streaming mode: Send actual data values
                    self.log_message(f"[DEBUG] handle_event called with data: {data}")
                    # Parse the incoming data
                    value, value_type = self._parse_value(data)
                    self.log_message(f"[DEBUG] Parsed value: {value} (type: {value_type})")
                    
                    if value is None:
                        self.log_message("⚠️ Received empty data, skipping OSC send")
                        return
                    
                    # Update last sent data for display
                    with self._lock:
                        self.last_sent_data = f"{value} ({value_type}, streaming mode)"
                    
                    # Send OSC message
                    if self.osc_client:
                        try:
                            self.log_message(f"[DEBUG] Sending OSC message: {self.osc_address} = {value}")
                            self.osc_client.send_message(self.osc_address, value)
                            self.log_message(f"OSC Sent (streaming): {self.osc_address} = {value}")
                            # Use the proper logging callback for OSC messages
                            if hasattr(self, 'log_callback') and self.log_callback:
                                self.log_callback(f"OSC SENT: {self.osc_address} = {value} ({value_type}) to {self.ip_address}:{self.port}")
                        except Exception as e:
                            self.log_message(f"❌ Failed to send OSC message: {e}")
                            self.connection_status = f"Send Error: {str(e)}"
                            # Try to reconnect
                            self._setup_osc_client()
                    else:
                        self.log_message(f"⚠️ OSC client not available, cannot send: {value}")
                
                else:
                    # Unknown mode - try to auto-detect from event data
                    if data.get('trigger', False):
                        # Looks like a trigger event, switch to trigger mode
                        self.set_input_classification("trigger")
                        # Recursively handle the event
                        self.handle_event(event, settings)
                    else:
                        # Looks like streaming data, switch to streaming mode
                        self.set_input_classification("streaming")
                        # Recursively handle the event
                        self.handle_event(event, settings)
                    
            except Exception as e:
                self.log_message(f"❌ Error handling event: {e}")

    def get_display_data(self):
        """Return data for GUI display fields"""
        with self._lock:
            return {
                'connection_status': self.connection_status,
                'last_sent_data': self.last_sent_data,
                'current_mode': self.current_mode
            }

    def update_display(self):
        """Update the GUI display with current status and data"""
        # This method can be called by the GUI to update status labels
        pass 