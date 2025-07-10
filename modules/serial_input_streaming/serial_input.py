import threading
import time
import serial
import serial.tools.list_ports
from modules.module_base import ModuleBase
import re

class SerialInputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        
        # Serial connection parameters
        self.port = config.get('port', '')
        self.baud_rate = int(config.get('baud_rate', 9600))
        
        # Serial connection state
        self.serial_connection = None
        self._running = False
        self._thread = None
        self._event_callbacks = set()
        
        # Data processing
        self.last_received_data = "No data received"
        self.connection_status = "Disconnected"
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Data buffer for handling partial messages
        self._buffer = ""
        
        self.log_message(f"Serial Input initialized - Port: {self.port}, Baud: {self.baud_rate}")

    def start(self):
        """Start the serial input module"""
        if self._running:
            self.log_message("⚠️ Serial module already running")
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log_message("🚀 Serial input module started")

    def stop(self):
        """Stop the serial input module"""
        self._running = False
        self._disconnect()
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        
        self.log_message("🛑 Serial input module stopped")

    def add_event_callback(self, callback):
        """Add a callback for data events"""
        self._event_callbacks.add(callback)

    def remove_event_callback(self, callback):
        """Remove a callback for data events"""
        self._event_callbacks.discard(callback)

    def update_config(self, config):
        """Update the module configuration"""
        old_port = self.port
        old_baud = self.baud_rate
        
        self.port = config.get('port', self.port)
        self.baud_rate = int(config.get('baud_rate', self.baud_rate))
        
        # If port or baud rate changed, reconnect
        if old_port != self.port or old_baud != self.baud_rate:
            self.log_message(f"🔄 Serial config updated - Port: {self.port}, Baud: {self.baud_rate}")
            if self._running:
                self._reconnect()

    def auto_configure(self):
        """
        If no port is set, select the first available port and update config.
        """
        if not self.port:
            ports = self.get_available_ports()
            if ports:
                self.port = ports[0]
                self.config['port'] = self.port
                self.log_message(f"[Auto-configure] Selected port: {self.port}")

    def _connect(self):
        """Establish serial connection"""
        if not self.port:
            self.connection_status = "No port selected"
            return False
            
        try:
            self._disconnect()  # Close any existing connection
            
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                timeout=1,  # 1 second timeout for reads
                write_timeout=1,  # 1 second timeout for writes
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Wait a moment for connection to stabilize
            time.sleep(0.1)
            
            if self.serial_connection.is_open:
                self.connection_status = "Connected"
                self.log_message(f"✅ Connected to {self.port} at {self.baud_rate} baud")
                return True
            else:
                self.connection_status = "Connection failed"
                self.log_message(f"❌ Failed to connect to {self.port}")
                return False
                
        except serial.SerialException as e:
            self.connection_status = f"Error: {str(e)}"
            self.log_message(f"❌ Serial connection error: {e}")
            return False
        except Exception as e:
            self.connection_status = f"Error: {str(e)}"
            self.log_message(f"❌ Unexpected error connecting to {self.port}: {e}")
            return False

    def _disconnect(self):
        """Close serial connection"""
        if self.serial_connection and self.serial_connection.is_open:
            try:
                self.serial_connection.close()
                self.log_message(f"🔌 Disconnected from {self.port}")
            except Exception as e:
                self.log_message(f"⚠️ Error closing connection: {e}")
        
        self.serial_connection = None
        self.connection_status = "Disconnected"

    def _reconnect(self):
        """Reconnect to the serial port"""
        self.log_message("🔄 Reconnecting to serial port...")
        self._disconnect()
        time.sleep(0.5)  # Brief delay before reconnecting
        self._connect()

    def _parse_data(self, raw_data):
        """
        Parse incoming serial data and extract values.
        Handles integers, floats, and strings with proper trimming.
        """
        try:
            # Decode bytes to string
            if isinstance(raw_data, bytes):
                data_str = raw_data.decode('utf-8', errors='ignore')
            else:
                data_str = str(raw_data)
            
            # Strip whitespace from beginning and end
            data_str = data_str.strip()
            
            if not data_str:
                return None
            
            # Try to parse as different data types
            # First, try as integer
            try:
                if data_str.isdigit() or (data_str.startswith('-') and data_str[1:].isdigit()):
                    return str(int(data_str))
            except ValueError:
                pass
            
            # Try as float
            try:
                float_val = float(data_str)
                # If it's a whole number, return as integer string
                if float_val.is_integer():
                    return str(int(float_val))
                else:
                    return str(float_val)
            except ValueError:
                pass
            
            # If not a number, return as string (already stripped)
            return data_str
            
        except Exception as e:
            self.log_message(f"⚠️ Error parsing data '{raw_data}': {e}")
            return None

    def _run(self):
        """Main serial reading loop"""
        while self._running:
            try:
                # Try to connect if not connected
                if not self.serial_connection or not self.serial_connection.is_open:
                    if not self._connect():
                        time.sleep(2)  # Wait before retrying
                        continue
                
                # Read data from serial port
                if self.serial_connection and self.serial_connection.in_waiting > 0:
                    try:
                        # Read available data
                        data = self.serial_connection.read(self.serial_connection.in_waiting)
                        
                        if data:
                            # Add to buffer and process
                            self._buffer += data.decode('utf-8', errors='ignore')
                            
                            # Process complete lines or chunks
                            lines = self._buffer.split('\n')
                            self._buffer = lines.pop()  # Keep incomplete line in buffer
                            
                            for line in lines:
                                line = line.strip()
                                if line:  # Skip empty lines
                                    parsed_value = self._parse_data(line)
                                    if parsed_value is not None:
                                        self._handle_data(parsed_value)
                                        
                    except serial.SerialException as e:
                        self.log_message(f"⚠️ Serial read error: {e}")
                        self._reconnect()
                        continue
                    except Exception as e:
                        self.log_message(f"⚠️ Error processing serial data: {e}")
                        continue
                
                # Small delay to prevent busy waiting
                time.sleep(0.01)
                
            except Exception as e:
                self.log_message(f"❌ Error in serial read loop: {e}")
                time.sleep(1)

    def _handle_data(self, value):
        """Handle parsed data and send to callbacks"""
        with self._lock:
            self.last_received_data = value
        
        # Create event data
        event = {
            'value': value,
            'timestamp': time.time(),
            'port': self.port,
            'baud_rate': self.baud_rate,
            'stream': True
        }
        
        # Send to all callbacks
        for callback in list(self._event_callbacks):
            try:
                callback(event)
            except Exception as e:
                self.log_message(f"❌ Error in serial event callback: {e}")

    def get_display_data(self):
        """Return data for GUI display fields"""
        with self._lock:
            return {
                'connection_status': self.connection_status,
                'incoming_data': self.last_received_data
            }

    @staticmethod
    def get_available_ports():
        """Get list of available serial ports"""
        try:
            ports = []
            for port in serial.tools.list_ports.comports():
                ports.append(port.device)
            return ports
        except Exception:
            return []

    def update_display(self):
        """Update the GUI display with current status and data"""
        # This method can be called by the GUI to update status labels
        pass 