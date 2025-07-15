import csv
import os
import threading
import socket
from modules.module_base import ModuleBase
import serial  # pyserial
import sacn

# Debug print to confirm module is being loaded
print("🔧 DMX Output module file loaded successfully")

def get_available_serial_ports():
    """Get list of available serial ports for dropdown."""
    try:
        import serial.tools.list_ports
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]
    except Exception:
        # Fallback to common ports if list_ports fails
        return ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8"]

ARTNET_PORT = 6454
SACN_PORT = 5568
DMX_CHANNELS = 512

class DMXOutputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.protocol = config.get('protocol', 'sacn')
        self.csv_file = config.get('csv_file', '')
        self.universe = int(config.get('universe', 1))
        self.ip_address = config.get('ip_address', '127.0.0.1')
        self.port = int(config.get('port', SACN_PORT))
        self.serial_port = config.get('serial_port', 'COM1')
        self.baud_rate = 57600  # Hardcoded for serial protocol
        self.net = int(config.get('net', 0))
        self.subnet = int(config.get('subnet', 0))
        self.dmx_frames = []
        self.current_frame = "No frame received"
        self._load_csv()
        self._setup_protocol()
        self._lock = threading.Lock()
        self.log_message(f"DMX Output initialized with protocol: {self.protocol}")

    def _load_csv(self):
        # Try to load the CSV, fallback to default if malformed or missing
        path = self.csv_file or os.path.join(os.path.dirname(__file__), 'default_dmx.csv')
        try:
            with open(path, 'r', newline='') as f:
                reader = csv.reader(f)
                self.dmx_frames = []
                for row in reader:
                    # Pad/truncate to 512 channels, default missing to 0
                    frame = [(int(val) if val else 0) for val in row[:DMX_CHANNELS]]
                    if len(frame) < DMX_CHANNELS:
                        frame += [0] * (DMX_CHANNELS - len(frame))
                    self.dmx_frames.append(frame)
            if not self.dmx_frames:
                raise ValueError('CSV contained no frames')
            self.log_message(f"Loaded {len(self.dmx_frames)} DMX frames from CSV: {path}")
        except Exception as e:
            # Fallback to default
            self.log_message(f"Error loading CSV '{path}': {e}. Using default.")
            default_path = os.path.join(os.path.dirname(__file__), 'default_dmx.csv')
            with open(default_path, 'r', newline='') as f:
                reader = csv.reader(f)
                self.dmx_frames = []
                for row in reader:
                    frame = [(int(val) if val else 0) for val in row[:DMX_CHANNELS]]
                    if len(frame) < DMX_CHANNELS:
                        frame += [0] * (DMX_CHANNELS - len(frame))
                    self.dmx_frames.append(frame)
            self.log_message(f"Loaded {len(self.dmx_frames)} DMX frames from default CSV.")

    def _setup_protocol(self):
        self._close_protocol()
        if self.protocol == 'serial':
            try:
                # DMX512 uses 57600 baud, 8 data bits, 2 stop bits, no parity
                self.serial_conn = serial.Serial(
                    port=self.serial_port,
                    baudrate=57600,  # DMX512 baud rate as originally specified
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    stopbits=serial.STOPBITS_TWO,
                    timeout=1
                )
                self.log_message(f"Serial port opened: {self.serial_port} @ 57600 baud (DMX512)")
            except Exception as e:
                self.serial_conn = None
                self.log_message(f"Error opening serial port: {e}")
        elif self.protocol == 'artnet':
            try:
                self.artnet_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.log_message(f"Art-Net UDP socket ready: {self.ip_address}:{self.port}")
            except Exception as e:
                self.artnet_sock = None
                self.log_message(f"Error creating Art-Net socket: {e}")
        elif self.protocol == 'sacn':
            try:
                self.sacn_sender = sacn.sACNsender()
                self.sacn_sender.start()
                self.sacn_universe = self.sacn_sender.activate_output(self.universe)
                if self.sacn_universe is not None:
                    self.sacn_universe.multicast = True
                    # sACN multicast doesn't need destination IP
                self.log_message(f"sACN multicast sender started for universe {self.universe}")
            except Exception as e:
                self.sacn_sender = None
                self.sacn_universe = None
                self.log_message(f"Error starting sACN sender: {e}")

    def _close_protocol(self):
        # Clean up any protocol resources
        if hasattr(self, 'serial_conn') and self.serial_conn:
            try:
                self.serial_conn.close()
                self.log_message("🛑 Serial connection closed")
            except Exception as e:
                self.log_message(f"⚠️ Error closing serial connection: {e}")
            self.serial_conn = None
        if hasattr(self, 'artnet_sock') and self.artnet_sock:
            try:
                self.artnet_sock.close()
                self.log_message("🛑 Art-Net socket closed")
            except Exception as e:
                self.log_message(f"⚠️ Error closing Art-Net socket: {e}")
            self.artnet_sock = None
        if hasattr(self, 'sacn_sender') and self.sacn_sender:
            try:
                # Add timeout to prevent hanging during shutdown
                import threading
                import time
                
                def stop_sacn():
                    try:
                        if self.sacn_sender:
                            self.sacn_sender.stop()
                    except Exception:
                        pass
                
                # Start sACN stop in a separate thread with timeout
                stop_thread = threading.Thread(target=stop_sacn, daemon=True)
                stop_thread.start()
                stop_thread.join(timeout=2)  # Wait max 2 seconds
                
                if stop_thread.is_alive():
                    self.log_message("⚠️ sACN sender stop timed out, forcing cleanup")
                else:
                    self.log_message("🛑 sACN sender stopped")
                    
            except Exception as e:
                self.log_message(f"⚠️ Error stopping sACN sender: {e}")
            self.sacn_sender = None
            self.sacn_universe = None

    def update_config(self, config):
        # Update config and reload protocol/CSV if needed
        self.protocol = config.get('protocol', self.protocol)
        self.csv_file = config.get('csv_file', self.csv_file)
        self.universe = int(config.get('universe', self.universe))
        
        # Only update IP/port for Art-Net (not sACN)
        if self.protocol == 'artnet':
            self.ip_address = config.get('ip_address', self.ip_address)
            self.port = int(config.get('port', self.port))
        
        self.serial_port = config.get('serial_port', self.serial_port)
        # baud_rate is hardcoded to 57600
        self.net = int(config.get('net', self.net))
        self.subnet = int(config.get('subnet', self.subnet))
        self._load_csv()
        self._setup_protocol()

    def handle_event(self, data):
        # Expecting a frame number in the event data
        try:
            frame_number = int(data.get('value', 0))
        except Exception:
            frame_number = 0
        if not self.dmx_frames:
            self.log_message("No DMX frames loaded!")
            return
        # Modulo frame number to loop through available frames
        frame_index = frame_number % len(self.dmx_frames)
        frame = self.dmx_frames[frame_index]
        
        # Update current frame display
        with self._lock:
            self.current_frame = f"Frame {frame_index} (Input: {frame_number})"
        
        # Log every frame for debugging
        self.log_message(f"🎭 Received event: frame {frame_number}, sending DMX frame {frame_index} via {self.protocol}")
        
        if self.protocol == 'serial' and hasattr(self, 'serial_conn') and self.serial_conn:
            try:
                # Send DMX data with proper protocol formatting
                if self._send_dmx_serial(frame):
                    self.log_message(f"✅ Serial DMX frame sent successfully")
                else:
                    self.log_message(f"⚠️ Failed to send serial DMX frame")
            except Exception as e:
                self.log_message(f"Serial send error: {e}")
        elif self.protocol == 'artnet' and hasattr(self, 'artnet_sock') and self.artnet_sock:
            try:
                artnet_packet = self._build_artnet_packet(frame)
                self.artnet_sock.sendto(artnet_packet, (self.ip_address, self.port))
                self.log_message(f"✅ Art-Net frame sent successfully")
            except Exception as e:
                self.log_message(f"Art-Net send error: {e}")
        elif self.protocol == 'sacn' and hasattr(self, 'sacn_universe') and self.sacn_universe:
            try:
                self.sacn_universe.dmx_data = frame
                self.log_message(f"✅ sACN frame sent successfully")
            except Exception as e:
                self.log_message(f"sACN send error: {e}")
        else:
            self.log_message(f"⚠️ No valid protocol connection for {self.protocol}")

    def _build_dmx_packet(self, dmx_data):
        """
        Build DMX packet for serial transmission using the working protocol format.
        Format: 0x7E + 0x06 + length_low + length_high + 0x00 + data + 0xE7
        """
        packet = bytearray()
        
        # Start marker
        packet.append(0x7E)
        packet.append(0x06)
        
        # Data length (513 bytes)
        data_length = 513
        packet.append(data_length & 0xFF)  # Low byte
        packet.append((data_length >> 8) & 0xFF)  # High byte
        
        # Start code
        packet.append(0x00)
        
        # DMX data (512 channels, starting from index 1)
        packet.extend(dmx_data[:DMX_CHANNELS])
        
        # End marker
        packet.append(0xE7)
        
        return packet

    def _send_dmx_serial(self, dmx_data):
        """
        Send DMX data via serial using the working protocol format.
        """
        if not self.serial_conn or not self.serial_conn.is_open:
            self.log_message("⚠️ Serial connection not available")
            return False
        
        try:
            # Build DMX packet with proper format
            dmx_packet = self._build_dmx_packet(dmx_data)
            
            # Send the packet
            self.serial_conn.write(dmx_packet)
            self.serial_conn.flush()
            
            return True
            
        except Exception as e:
            self.log_message(f"Serial DMX send error: {e}")
            return False

    def _build_artnet_packet(self, dmx_data):
        # Build a minimal Art-Net DMX packet
        # See Art-Net specification for details
        packet = bytearray()
        packet.extend(b'Art-Net\x00')  # 8 bytes
        packet.extend((0x00, 0x50))    # OpCode ArtDMX (0x5000)
        packet.extend((0x00, 0x0e))    # Protocol version 14
        packet.append(0)  # Sequence (set to 0)
        packet.append(0)  # Physical
        # Universe (low byte, high byte)
        universe = self.universe if hasattr(self, 'universe') else 0
        packet.append(universe & 0xFF)
        packet.append((universe >> 8) & 0xFF)
        # Length (high byte, low byte)
        packet.append((DMX_CHANNELS >> 8) & 0xFF)
        packet.append(DMX_CHANNELS & 0xFF)
        # DMX data
        packet.extend(dmx_data[:DMX_CHANNELS])
        return packet

    def start(self):
        """Start the DMX output module."""
        super().start()
        self.log_message(f"🎭 DMX Output started with protocol: {self.protocol}")
        # Ensure protocol is properly set up
        self._setup_protocol()
        self.log_message(f"🎭 DMX Output ready to send frames")

    def get_display_data(self):
        """Return data for GUI display fields"""
        with self._lock:
            return {
                'current_frame': self.current_frame
            }

    def get_field_options(self, field_name):
        """Return options for a given field (for dropdowns, etc.), or None."""
        if field_name == "serial_port":
            return get_available_serial_ports()
        return None

    def stop(self):
        """
        Stop the DMX Output module and clean up resources.
        Ensures all threads and resources are properly released.
        """
        super().stop()
        self._close_protocol()
        self.log_message("DMX Output module stopped.")

# Debug print to confirm class is defined
print("🔧 DMXOutputModule class defined successfully") 