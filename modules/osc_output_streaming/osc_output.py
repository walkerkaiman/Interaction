import socket
import threading
import time
from modules.module_base import ModuleBase
from pythonosc import udp_client

class OSCOutputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        
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
        
        # Initialize OSC client
        self._setup_osc_client()
        
        self.log_message(f"OSC Output initialized - IP: {self.ip_address}, Port: {self.port}, Address: {self.osc_address}")

    def start(self):
        """Start the OSC output module"""
        self.log_message("🚀 OSC output module started")

    def stop(self):
        """Stop the OSC output module"""
        self._disconnect()
        self.log_message("🛑 OSC output module stopped")

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
            
            # Strip whitespace
            value = value.strip()
            
            if not value:
                return None, "empty"
            
            # Check if it's a float (contains decimal point)
            if '.' in value:
                try:
                    float_val = float(value)
                    return float_val, "float"
                except ValueError:
                    # If float conversion fails, return as string
                    return value, "string"
            
            # Check if it's an integer
            try:
                int_val = int(value)
                return int_val, "integer"
            except ValueError:
                # If integer conversion fails, return as string
                return value, "string"
                
        except Exception as e:
            self.log_message(f"⚠️ Error parsing value '{data}': {e}")
            return str(data), "string"

    def handle_event(self, data):
        """Handle incoming events and send OSC messages"""
        try:
            # Parse the incoming data
            value, value_type = self._parse_value(data)
            
            if value is None:
                self.log_message("⚠️ Received empty data, skipping OSC send")
                return
            
            # Update last sent data for display
            with self._lock:
                self.last_sent_data = f"{value} ({value_type})"
            
            # Send OSC message
            if self.osc_client:
                try:
                    self.osc_client.send_message(self.osc_address, value)
                    self.log_message(f"OSC Sent: {self.osc_address} = {value}")
                    print(f"[{time.strftime('%H:%M:%S')}] 📡 OSC SENT: {self.osc_address} = {value} ({value_type}) to {self.ip_address}:{self.port}")
                except Exception as e:
                    self.log_message(f"❌ Failed to send OSC message: {e}")
                    self.connection_status = f"Send Error: {str(e)}"
                    # Try to reconnect
                    self._setup_osc_client()
            else:
                self.log_message(f"⚠️ OSC client not available, cannot send: {value}")
                
        except Exception as e:
            self.log_message(f"❌ Error handling event: {e}")

    def get_display_data(self):
        """Return data for GUI display fields"""
        with self._lock:
            return {
                'connection_status': self.connection_status,
                'last_sent_data': self.last_sent_data
            }

    def update_display(self):
        """Update the GUI display with current status and data"""
        # This method can be called by the GUI to update status labels
        pass 