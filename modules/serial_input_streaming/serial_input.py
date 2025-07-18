import serial
import threading
import time
from modules.module_base import DedicatedThreadModule

class SerialInputModule(DedicatedThreadModule):
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        
        # Serial configuration
        self.serial_port = config.get('serial_port', 'COM1')
        self.baud_rate = int(config.get('baud_rate', 9600))
        
        # Serial connection
        self.serial_conn = None
        self.connection_status = "Disconnected"
        self.last_received_data = "No data received"
        
        # Thread/event management handled by DedicatedThreadModule
        
        self.log_message(f"Serial Input initialized - Port: {self.serial_port}, Baud: {self.baud_rate}")

    # start/stop/wait_for_stop handled by DedicatedThreadModule

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
            self.log_message(f"✅ Connected to {self.serial_port} @ {self.baud_rate} baud")
            return True
        except Exception as e:
            self.connection_status = f"Error: {str(e)}"
            self.log_message(f"❌ Failed to connect to {self.serial_port}: {e}")
            return False

    def _close_serial(self):
        """Close serial connection"""
        if self.serial_conn:
            try:
                self.serial_conn.close()
                self.log_message(f"🔌 Disconnected from {self.serial_port}")
            except Exception as e:
                self.log_message(f"⚠️ Error closing serial connection: {e}")
            self.serial_conn = None
        self.connection_status = "Disconnected"

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
                            
                            # Emit streaming event
                            event_data = {
                                "value": data,
                                "timestamp": time.time()
                            }
                            self.emit_event(event_data)
                    except UnicodeDecodeError:
                        self.log_message("⚠️ Invalid data received (encoding error)")
                    except Exception as e:
                        self.log_message(f"⚠️ Error reading serial data: {e}")
                
                # Use event-driven wait instead of sleep
                if self._stop_event.wait(0.01):  # Wait 10ms or until stop signal
                    break
                    
            except Exception as e:
                self.log_message(f"❌ Error in serial loop: {e}")
                self._close_serial()
                # Use event-driven wait for reconnection
                if self._stop_event.wait(2):  # Wait 2 seconds or until stop signal
                    break

    def update_config(self, config):
        """Update the module configuration"""
        old_port = self.serial_port
        old_baud = self.baud_rate
        
        self.serial_port = config.get('serial_port', self.serial_port)
        self.baud_rate = int(config.get('baud_rate', self.baud_rate))
        
        # Reconnect if port or baud rate changed
        if old_port != self.serial_port or old_baud != self.baud_rate:
            self.log_message(f"🔄 Serial config updated - Port: {self.serial_port}, Baud: {self.baud_rate}")
            if self._running:
                self._close_serial()

    def auto_configure(self):
        """Set default values if not configured"""
        if not getattr(self, 'serial_port', None):
            self.serial_port = 'COM1'
            self.config['serial_port'] = 'COM1'
            self.log_message("[Auto-configure] Set default serial port: COM1")
        if not getattr(self, 'baud_rate', None):
            self.baud_rate = 9600
            self.config['baud_rate'] = 9600
            self.log_message("[Auto-configure] Set default baud rate: 9600")

    def get_display_data(self):
        """Return data for GUI display fields"""
        return {
            'connection_status': self.connection_status,
            'last_received_data': self.last_received_data
        } 