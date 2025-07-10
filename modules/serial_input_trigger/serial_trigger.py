import threading
import time
import serial
import serial.tools.list_ports
from modules.module_base import ModuleBase
import struct

class SerialTriggerModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        
        # Serial connection parameters
        self.port = config.get('port', '')
        self.baud_rate = int(config.get('baud_rate', 9600))
        
        # Logic parameters
        self.logic_operator = config.get('logic_operator', '>')
        self.threshold_value = float(config.get('threshold_value', 0))
        
        # Serial connection state
        self.serial_connection = None
        self._running = False
        self._thread = None
        self._event_callbacks = set()
        
        # Data processing
        self.current_value = None
        self.connection_status = "Disconnected"
        self.trigger_status = "Waiting"
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Data buffer for handling partial messages
        self._buffer = b""
        
        # Crossing detection state
        self._last_triggered = False
        self._crossing_state = {
            '<': False,  # True when value is below threshold
            '>': False   # True when value is above threshold
        }
        
        self.log_message(f"Serial Trigger initialized - Port: {self.port}, Baud: {self.baud_rate}, Logic: {self.logic_operator} {self.threshold_value}")

    def start(self):
        """Start the serial trigger module"""
        if self._running:
            self.log_message("⚠️ Serial trigger module already running")
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.log_message("🚀 Serial trigger module started")

    def stop(self):
        """Stop the serial trigger module"""
        self._running = False
        self._disconnect()
        
        if self._thread:
            self._thread.join(timeout=2)
            self._thread = None
        
        self.log_message("🛑 Serial trigger module stopped")

    def add_event_callback(self, callback):
        """Add a callback for trigger events"""
        self._event_callbacks.add(callback)

    def remove_event_callback(self, callback):
        """Remove a callback for trigger events"""
        self._event_callbacks.discard(callback)

    def update_config(self, config):
        """Update the module configuration"""
        old_port = self.port
        old_baud = self.baud_rate
        old_operator = self.logic_operator
        old_threshold = self.threshold_value
        
        self.port = config.get('port', self.port)
        self.baud_rate = int(config.get('baud_rate', self.baud_rate))
        self.logic_operator = config.get('logic_operator', self.logic_operator)
        self.threshold_value = float(config.get('threshold_value', self.threshold_value))
        
        # Reset crossing state if logic parameters changed
        if old_operator != self.logic_operator or old_threshold != self.threshold_value:
            self._reset_crossing_state()
            self.log_message(f"🔄 Logic updated: {self.logic_operator} {self.threshold_value}")
        
        # If port or baud rate changed, reconnect
        if old_port != self.port or old_baud != self.baud_rate:
            self.log_message(f"🔄 Serial config updated - Port: {self.port}, Baud: {self.baud_rate}")
            if self._running:
                self._reconnect()

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

    def _reset_crossing_state(self):
        """Reset the crossing detection state"""
        with self._lock:
            self._crossing_state = {'<': False, '>': False}
            self._last_triggered = False
            self.trigger_status = "Waiting"

    def _parse_serial_data(self, raw_data):
        """
        Parse incoming serial data and convert to numeric value.
        Assumes the data is bytes representing an int or float.
        """
        try:
            # Try to parse as different numeric formats
            # First, try as 4-byte float
            if len(raw_data) >= 4:
                try:
                    float_val = struct.unpack('f', raw_data[:4])[0]
                    return float_val, "float"
                except struct.error:
                    pass
            
            # Try as 4-byte integer
            if len(raw_data) >= 4:
                try:
                    int_val = struct.unpack('i', raw_data[:4])[0]
                    return int_val, "integer"
                except struct.error:
                    pass
            
            # Try as 2-byte integer
            if len(raw_data) >= 2:
                try:
                    int_val = struct.unpack('h', raw_data[:2])[0]
                    return int_val, "integer"
                except struct.error:
                    pass
            
            # Try as 1-byte integer
            if len(raw_data) >= 1:
                try:
                    int_val = struct.unpack('b', raw_data[:1])[0]
                    return int_val, "integer"
                except struct.error:
                    pass
            
            # If all else fails, try to decode as string and convert
            try:
                data_str = raw_data.decode('utf-8', errors='ignore').strip()
                if '.' in data_str:
                    return float(data_str), "float"
                else:
                    return int(data_str), "integer"
            except (ValueError, UnicodeDecodeError):
                pass
            
            return None, "unknown"
            
        except Exception as e:
            self.log_message(f"⚠️ Error parsing serial data: {e}")
            return None, "error"

    def _evaluate_logic(self, value):
        """
        Evaluate the logic condition and determine if a trigger should fire.
        Returns (should_trigger, reason)
        """
        if value is None:
            return False, "No valid data"
        
        if self.logic_operator == "=":
            # Equals logic: trigger when value exactly matches threshold
            if abs(value - self.threshold_value) < 0.001:  # Small tolerance for floats
                return True, f"Value {value} equals threshold {self.threshold_value}"
            return False, f"Value {value} != threshold {self.threshold_value}"
        
        elif self.logic_operator == "<":
            # Less than logic: trigger when crossing below threshold
            current_below = value < self.threshold_value
            was_below = self._crossing_state['<']
            
            if current_below and not was_below:
                # Just crossed below threshold
                self._crossing_state['<'] = True
                return True, f"Value {value} crossed below {self.threshold_value}"
            elif not current_below and was_below:
                # Just crossed above threshold (reset state)
                self._crossing_state['<'] = False
                return False, f"Value {value} crossed above {self.threshold_value} (reset)"
            else:
                # No crossing
                self._crossing_state['<'] = current_below
                return False, f"Value {value} {'below' if current_below else 'above'} {self.threshold_value}"
        
        elif self.logic_operator == ">":
            # Greater than logic: trigger when crossing above threshold
            current_above = value > self.threshold_value
            was_above = self._crossing_state['>']
            
            if current_above and not was_above:
                # Just crossed above threshold
                self._crossing_state['>'] = True
                return True, f"Value {value} crossed above {self.threshold_value}"
            elif not current_above and was_above:
                # Just crossed below threshold (reset state)
                self._crossing_state['>'] = False
                return False, f"Value {value} crossed below {self.threshold_value} (reset)"
            else:
                # No crossing
                self._crossing_state['>'] = current_above
                return False, f"Value {value} {'above' if current_above else 'below'} {self.threshold_value}"
        
        return False, f"Unknown operator: {self.logic_operator}"

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
                            self._buffer += data
                            
                            # Process complete chunks (assuming 4-byte values)
                            while len(self._buffer) >= 4:
                                chunk = self._buffer[:4]
                                self._buffer = self._buffer[4:]
                                
                                # Parse the chunk
                                value, value_type = self._parse_serial_data(chunk)
                                
                                if value is not None:
                                    self._handle_value(value, value_type)
                                    
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

    def _handle_value(self, value, value_type):
        """Handle parsed value and evaluate logic"""
        with self._lock:
            self.current_value = value
        
        # Evaluate logic condition
        should_trigger, reason = self._evaluate_logic(value)
        
        with self._lock:
            if should_trigger:
                self.trigger_status = f"Triggered: {reason}"
                self._last_triggered = True
            else:
                self.trigger_status = f"Waiting: {reason}"
        
        # Fire trigger if condition met
        if should_trigger:
            self._fire_trigger(value, value_type, reason)

    def _fire_trigger(self, value, value_type, reason):
        """Fire the trigger event"""
        # Create event data
        event = {
            'value': value,
            'value_type': value_type,
            'threshold': self.threshold_value,
            'operator': self.logic_operator,
            'reason': reason,
            'timestamp': time.time(),
            'trigger': True
        }
        
        self.log_message(f"🎯 TRIGGER: {reason} (Value: {value}, Type: {value_type})")
        
        # Send to all callbacks
        for callback in list(self._event_callbacks):
            try:
                callback(event)
            except Exception as e:
                self.log_message(f"❌ Error in trigger callback: {e}")

    def get_display_data(self):
        """Return data for GUI display fields"""
        with self._lock:
            return {
                'connection_status': self.connection_status,
                'current_value': f"{self.current_value:.3f}" if self.current_value is not None else "No data",
                'trigger_status': self.trigger_status
            }

    def update_display(self):
        """Update the GUI display with current status and data"""
        # This method can be called by the GUI to update status labels
        pass

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