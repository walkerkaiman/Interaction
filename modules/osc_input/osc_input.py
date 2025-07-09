from modules.module_base import ModuleBase
from modules.osc_input.osc_server_manager import osc_manager

class OSCInput(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.port = int(self.config.get("port", 8000))
        self.address = self.config.get("address", "/trigger")
        self.registered = False
        self.callback_ref = None  # Store reference to our callback

    def start(self):
        """Register with the shared OSC server manager"""
        if not self.registered:
            self.callback_ref = self._on_message  # Store reference
            osc_manager.register_callback(self.port, self.address, self.callback_ref)
            self.registered = True
            self.log_message(f"🔧 Registered with shared OSC server - Port: {self.port}, Address: {self.address}", level="show_mode")

    def stop(self):
        """Unregister from the shared OSC server manager"""
        if self.registered:
            osc_manager.unregister_callback(self.port, self.address, self.callback_ref)
            self.registered = False
            self.callback_ref = None
            self.log_message(f"🛑 Unregistered from shared OSC server - Port: {self.port}, Address: {self.address}", level="show_mode")

    def handle_button_action(self, action_name):
        if action_name == "restart_server":
            self.log_message("🔄 Restarting OSC server registration...", level="show_mode")
            self.log_message(f"🔧 Current config - Port: {self.port}, Address: {self.address}", level="verbose")
            
            # Re-register with the shared server
            if self.registered:
                self.log_message(f"🛑 Stopping with address: {self.address}", level="verbose")
                # Unregister from the current address
                osc_manager.unregister_callback(self.port, self.address, self.callback_ref)
                self.registered = False
                self.callback_ref = None
            self.log_message(f"🔧 Starting with address: {self.address}", level="verbose")
            self.start()

    def _on_message(self, data):
        """Handle incoming OSC message"""
        actual_address = data.get('address', self.address)
        self.log_message(f"📥 Received OSC message on {actual_address}: {data.get('args', [])}", level="output_trigger")
        self.emit_event(data)

    def update_config(self, new_config):
        """Update configuration and re-register if needed"""
        old_port = self.port
        old_address = self.address
        
        self.log_message(f"🔄 Updating config - Old: port={old_port}, address='{old_address}'", level="verbose")
        
        super().update_config(new_config)
        
        self.port = int(self.config.get("port", 8000))
        self.address = self.config.get("address", "/trigger")
        
        self.log_message(f"🔄 New config - Port: {self.port}, Address: '{self.address}'", level="verbose")
        
        # If port or address changed, re-register
        if old_port != self.port or old_address != self.address:
            self.log_message(f"🔄 Configuration changed (port: {old_port}->{self.port}, address: '{old_address}'->'{self.address}'), re-registering...", level="show_mode")
            if self.registered:
                # Unregister from the OLD address, not the new one
                self.log_message(f"🛑 Unregistering from old address: {old_address}", level="verbose")
                osc_manager.unregister_callback(old_port, old_address, self.callback_ref)
                self.registered = False
                self.callback_ref = None
            self.start()
        else:
            self.log_message(f"🔄 No configuration changes detected", level="verbose")
