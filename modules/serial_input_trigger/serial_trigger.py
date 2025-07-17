import serial
import threading
import time
from modules.module_base import ModuleBase
from module_loader import get_thread_pool
from main import broadcast_log_message

class SerialTriggerModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        
        # Serial configuration
        self.serial_port = config.get('serial_port', 'COM1')
        self.baud_rate = int(config.get('baud_rate', 9600))
        self.logic_operator = config.get('logic_operator', '>')
        self.threshold_value = float(config.get('threshold_value', 0.5))
        
        # Serial connection
        self.serial_conn = None
        self.connection_status = "Disconnected"
        self.last_received_data = "No data received"
        
        # Thread management
        self._thread = None
        self._running = False
        
        # Get optimized thread pool
        self.thread_pool = get_thread_pool()
        
        # Event-driven timing
        self._stop_event = threading.Event()
        
        broadcast_log_message(f"Serial Trigger initialized - Port: {self.serial_port}, Baud: {self.baud_rate}", module=self.__class__.__name__, category='serial')

    def start(self):
        super().start()
        if not self._running:
            self._running = True
            self._stop_event.clear()
            # Use optimized thread pool instead of creating new thread
            self._thread = self.thread_pool.submit_realtime(self._run)
            broadcast_log_message("🔌 Serial trigger started", module=self.__class__.__name__, category='serial')

    def stop(self):
        self._running = False
        self._stop_event.set()  # Signal thread to stop
        if self._thread:
            self._thread.cancel()  # Cancel the thread pool task
        super().stop()
        self._close_serial()
        broadcast_log_message(f"🛑 Serial trigger stopped (instance {self.instance_id})", module=self.__class__.__name__, category='serial')

    def wait_for_stop(self):
        """
        Wait for the serial reading thread to finish.
        """
        # If using a thread pool future, wait for it to finish if possible
        if self._thread and hasattr(self._thread, 'result'):
            try:
                self._thread.result(timeout=1)
            except Exception:
                pass
        self._thread = None

    def _open_serial(self):
        """Open serial connection with event-driven retry logic"""
        try:
            if self.serial_conn and self.serial_conn.is_open:
                return True
                
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=1
            )
            self.connection_status = "Connected"
            broadcast_log_message(f"✅ Connected to {self.serial_port} @ {self.baud_rate} baud", module=self.__class__.__name__, category='serial')
            return True
        except Exception as e:
            self.connection_status = f"Error: {str(e)}"
            broadcast_log_message(f"❌ Failed to connect to {self.serial_port}: {e}", module=self.__class__.__name__, category='serial')
            return False

    def _close_serial(self):
        """Close serial connection"""
        if self.serial_conn:
            try:
                self.serial_conn.close()
                broadcast_log_message(f"🔌 Disconnected from {self.serial_port}", module=self.__class__.__name__, category='serial')
            except Exception as e:
                broadcast_log_message(f"⚠️ Error closing serial connection: {e}", module=self.__class__.__name__, category='serial')
            self.serial_conn = None
        self.connection_status = "Disconnected"

    def _check_trigger_condition(self, value):
        """Check if the value meets the trigger condition"""
        try:
            numeric_value = float(value)
            if self.logic_operator == '>':
                return numeric_value > self.threshold_value
            elif self.logic_operator == '<':
                return numeric_value < self.threshold_value
            elif self.logic_operator == '>=':
                return numeric_value >= self.threshold_value
            elif self.logic_operator == '<=':
                return numeric_value <= self.threshold_value
            elif self.logic_operator == '==':
                return numeric_value == self.threshold_value
            elif self.logic_operator == '!=':
                return numeric_value != self.threshold_value
            else:
                return False
        except (ValueError, TypeError):
            return False

    def _run(self):
        """Main serial reading loop - optimized with event-driven approach"""
        while self._running and not self._stop_event.is_set():
            try:
                # Try to open connection if not connected
                if not self._open_serial():
                    # Use event-driven wait instead of sleep
                    if self._stop_event.wait(2):  # Wait 2 seconds or until stop signal
                        break
                    continue
                
                # Read data with timeout
                if self.serial_conn and self.serial_conn.in_waiting > 0:
                    try:
                        data = self.serial_conn.readline().decode('utf-8').strip()
                        if data:
                            self.last_received_data = data
                            
                            # Check trigger condition
                            if self._check_trigger_condition(data):
                                event_data = {
                                    "value": data,
                                    "trigger": True,
                                    "threshold": self.threshold_value,
                                    "operator": self.logic_operator
                                }
                                self.emit_event(event_data)
                                broadcast_log_message(f"🎯 Trigger fired: {data} {self.logic_operator} {self.threshold_value}", module=self.__class__.__name__, category='serial')
                            else:
                                # Emit non-trigger event for display updates
                                event_data = {
                                    "value": data,
                                    "trigger": False,
                                    "threshold": self.threshold_value,
                                    "operator": self.logic_operator
                                }
                                self.emit_event(event_data)
                    except UnicodeDecodeError:
                        broadcast_log_message("⚠️ Invalid data received (encoding error)", module=self.__class__.__name__, category='serial')
                    except Exception as e:
                        broadcast_log_message(f"⚠️ Error reading serial data: {e}", module=self.__class__.__name__, category='serial')
                
                # Use event-driven wait instead of sleep
                if self._stop_event.wait(0.01):  # Wait 10ms or until stop signal
                    break
                    
            except Exception as e:
                broadcast_log_message(f"❌ Error in serial loop: {e}", module=self.__class__.__name__, category='serial')
                self._close_serial()
                # Use event-driven wait for reconnection
                if self._stop_event.wait(2):  # Wait 2 seconds or until stop signal
                    break

    def update_config(self, config):
        """Update the module configuration"""
        old_port = self.serial_port
        old_baud = self.baud_rate
        old_operator = self.logic_operator
        old_threshold = self.threshold_value
        
        self.serial_port = config.get('serial_port', self.serial_port)
        self.baud_rate = int(config.get('baud_rate', self.baud_rate))
        self.logic_operator = config.get('logic_operator', self.logic_operator)
        self.threshold_value = float(config.get('threshold_value', self.threshold_value))
        
        # Reconnect if port or baud rate changed
        if old_port != self.serial_port or old_baud != self.baud_rate:
            broadcast_log_message(f"🔄 Serial config updated - Port: {self.serial_port}, Baud: {self.baud_rate}", module=self.__class__.__name__, category='serial')
            if self._running:
                self._close_serial()

    def auto_configure(self):
        """Set default values if not configured"""
        if not getattr(self, 'serial_port', None):
            self.serial_port = 'COM1'
            self.config['serial_port'] = 'COM1'
            broadcast_log_message("[Auto-configure] Set default serial port: COM1", module=self.__class__.__name__, category='serial')
        if not getattr(self, 'baud_rate', None):
            self.baud_rate = 9600
            self.config['baud_rate'] = 9600
            broadcast_log_message("[Auto-configure] Set default baud rate: 9600", module=self.__class__.__name__, category='serial')
        if not getattr(self, 'logic_operator', None):
            self.logic_operator = '>'
            self.config['logic_operator'] = '>'
            broadcast_log_message("[Auto-configure] Set default logic operator: >", module=self.__class__.__name__, category='serial')
        if not getattr(self, 'threshold_value', None):
            self.threshold_value = 0.5
            self.config['threshold_value'] = 0.5
            broadcast_log_message("[Auto-configure] Set default threshold: 0.5", module=self.__class__.__name__, category='serial')

    def get_display_data(self):
        """Return data for GUI display fields"""
        return {
            'connection_status': self.connection_status,
            'last_received_data': self.last_received_data
        } 