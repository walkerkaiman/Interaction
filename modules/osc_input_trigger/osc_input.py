"""
OSC Input Module - Open Sound Control Message Receiver

This module implements an OSC (Open Sound Control) message receiver that listens
for OSC messages on a specified UDP port and address pattern. When messages are
received, they are converted to events and emitted to connected output modules.

Key Features:
1. UDP server listening for OSC messages
2. Configurable port and address pattern
3. Shared server management to avoid port conflicts
4. Automatic message parsing and event conversion
5. Support for multiple data types (float, string, etc.)

The OSC input module is designed to work with the shared OSC server manager
to allow multiple OSC input modules to listen on the same port but different
addresses without conflicts.

Author: Interaction Framework Team
License: MIT
"""

import socket
import threading
import time
from typing import Dict, Any, List, Optional
from pythonosc import dispatcher, osc_server
from modules.module_base import ModuleBase

# Import the shared OSC server manager
from modules.osc_input_trigger.osc_server_manager import OSCServerManager
# Import the shared input event router
from module_loader import input_event_router

class OSCInputModule(ModuleBase):
    """
    OSC (Open Sound Control) input module for receiving network messages.
    
    This module creates a UDP server that listens for OSC messages on a
    specified port and address pattern. When messages are received, they
    are parsed and converted to events that are emitted to connected
    output modules.
    
    The module uses the shared OSC server manager to avoid port conflicts
    when multiple OSC input modules are configured to listen on the same
    port but different addresses.
    
    Key Features:
    - Configurable UDP port and OSC address pattern
    - Shared server management for port conflict avoidance
    - Support for multiple OSC message data types
    - Automatic event conversion and emission
    - Thread-safe operation
    
    Configuration:
    - port (int): UDP port to listen on (default: 8000)
    - address (str): OSC address pattern to match (default: "/trigger")
    
    Event Format:
    The module emits events with the following structure:
    {
        "address": "/trigger",      # OSC address that was matched
        "args": [0.75],            # OSC message arguments
        "trigger": 0.75,           # First argument as trigger value
        "timestamp": 1234567890.123 # Message timestamp
    }
    """
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], 
                 log_callback=print):
        """
        Initialize the OSC input module.
        
        Args:
            config (Dict[str, Any]): Module configuration
            manifest (Dict[str, Any]): Module manifest
            log_callback: Function to call for logging
            
        Note: The configuration should contain 'port' and 'address' fields
        that specify the UDP port and OSC address pattern to listen for.
        """
        super().__init__(config, manifest, log_callback)
        
        # Extract configuration values with defaults
        self.port = config.get("port", 8000)
        self.address = config.get("address", "/trigger")
        
        # Server management
        self.server_manager = OSCServerManager()
        self.server_thread = None
        self.is_running = False
        
        # No internal callback list needed
        
        # Log initialization
        self.log_message(f"OSC Input initialized - Port: {self.port}, Address: {self.address}, Listening on all interfaces (0.0.0.0)")
    
    def start(self):
        """
        Start the OSC server and begin listening for messages.
        
        This method registers with the shared OSC server manager and starts
        listening for OSC messages on the configured port and address.
        When messages are received, they are converted to events and emitted
        to connected output modules.
        
        Note: The server uses a separate thread to avoid blocking the main
        application. The shared server manager handles port conflicts and
        allows multiple OSC input modules to share the same port.
        """
        super().start()
        
        try:
            # Register with the shared server manager
            # The server manager will automatically start the server if needed
            self.server_manager.register_callback(self.port, self.address, self._handle_osc_message)
            
            self.is_running = True
            self.log_message(f"✅ OSC server started on port {self.port}, listening for '{self.address}' on all interfaces (0.0.0.0)")
            
        except Exception as e:
            self.log_message(f"❌ Failed to start OSC server: {e}")
            self.is_running = False
    
    def stop(self):
        """
        Stop the OSC server and clean up resources.
        This method unregisters from the shared OSC server manager and
        stops listening for OSC messages. It ensures proper cleanup of
        network resources and threads.
        Note: The shared server manager will automatically stop the server
        if no other modules are listening on the same port.
        """
        super().stop()
        try:
            # Unregister from the shared server manager
            self.server_manager.unregister_callback(self.port, self.address, self._handle_osc_message)
            self.is_running = False
            self.log_message(f"🛑 OSC server stopped on port {self.port}")
            # Clean up any additional resources here (threads, files, etc.)
            # (If you add threads or open files in the future, stop/close them here.)
        except Exception as e:
            self.log_message(f"❌ Error stopping OSC server: {e}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update the module configuration and restart if necessary.
        
        This method is called by the GUI when the user changes the module
        configuration. If the port or address changes, the module will
        restart to apply the new settings.
        
        Args:
            new_config (Dict[str, Any]): New configuration dictionary
            
        Note: Configuration changes that affect the server (port or address)
        require a restart to take effect. The module handles this automatically.
        """
        old_port = self.port
        old_address = self.address
        
        # Update configuration
        super().update_config(new_config)
        
        # Extract new configuration values
        self.port = new_config.get("port", 8000)
        self.address = new_config.get("address", "/trigger")
        
        # Check if server settings changed
        if old_port != self.port or old_address != self.address:
            self.log_message(f"🔄 OSC configuration changed - Port: {self.port}, Address: {self.address}")
            
            # Restart the server with new settings
            if self.is_running:
                self.stop()
                time.sleep(0.1)  # Brief delay to ensure cleanup
                self.start()
    
    def auto_configure(self):
        """
        If no port or address is set, use defaults (port 8000, address /trigger).
        """
        if not getattr(self, 'port', None):
            self.port = 8000
            self.config['port'] = 8000
            self.log_message("[Auto-configure] Set default OSC port: 8000")
        if not getattr(self, 'address', None):
            self.address = '/trigger'
            self.config['address'] = '/trigger'
            self.log_message("[Auto-configure] Set default OSC address: /trigger")

    def set_event_callback(self, callback):
        """
        Register a callback to be called when an OSC event is received.
        """
        # Register with the global input event router
        input_event_router.register("osc_input", {"port": self.port, "address": self.address}, callback)

    def remove_event_callback(self, callback):
        """
        Remove a previously registered event callback.
        """
        input_event_router.unregister("osc_input", {"port": self.port, "address": self.address}, callback)

    def _handle_osc_message(self, address: str, *args):
        """
        Handle incoming OSC messages and convert them to events.
        
        This method is called by the OSC server when a message is received
        on the configured address. It converts the OSC message to an event
        and emits it to connected output modules.
        
        Args:
            address (str): OSC address that received the message
            *args: OSC message arguments (can be any data type)
            
        Note: This method is called from the OSC server thread, so it must
        be thread-safe. The event emission is handled by the base class
        which is designed to be thread-safe.
        
        Example OSC messages:
            /trigger 0.75          -> {"trigger": 0.75, "args": [0.75]}
            /play "test"           -> {"trigger": "test", "args": ["test"]}
            /volume 0.5 "main"     -> {"trigger": 0.5, "args": [0.5, "main"]}
        """
        try:
            # Log every received OSC message
            self.log_message(f"📡 OSC message received: {address} {args}")
            # Create event data from OSC message
            event = {
                "address": address,
                "args": list(args),
                "trigger": args[0] if args else None,
                "timestamp": time.time()
            }
            
            # Dispatch to the global input event router
            input_event_router.dispatch_event("osc_input", {"port": self.port, "address": self.address}, event)
            
        except Exception as e:
            self.log_message(f"❌ Error handling OSC message: {e}")
    
    def get_server_status(self) -> Dict[str, Any]:
        """
        Get the current server status information.
        
        Returns:
            Dict[str, Any]: Server status including port, address, and running state
            
        Note: This method is used by the GUI to display server status
        information to the user.
        """
        return {
            "port": self.port,
            "address": self.address,
            "interface": "0.0.0.0 (All Interfaces)",
            "running": self.is_running,
            "server_running": self.port in self.server_manager.servers
        }
    
    def test_trigger(self):
        """
        Send a test OSC message to trigger the module.
        
        This method is used for testing purposes. It simulates receiving
        an OSC message by calling the message handler directly with test data.
        
        Note: This is useful for testing the module without needing an
        external OSC client or network connection.
        """
        if self.is_running:
            self.log_message("🧪 Sending test OSC trigger")
            # Dispatch a test event to the global router
            input_event_router.dispatch_event("osc_input", {"port": self.port, "address": self.address}, {"address": self.address, "args": [0.75], "trigger": 0.75, "timestamp": time.time()})
        else:
            self.log_message("❌ Cannot test trigger - server not running")
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get the module configuration for saving to file.
        
        Returns:
            Dict[str, Any]: Module configuration dictionary
            
        Note: This method is used by the GUI to save module configuration.
        It excludes any runtime-only data that shouldn't be persisted.
        """
        return {
            "port": self.port,
            "address": self.address
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the module to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Module data dictionary
            
        Note: This method is used by the GUI to save the complete module
        state to the configuration file.
        """
        return {
            "type": "osc_input",
            "config": self.get_output_config()
        }

    def get_field_label(self, field_name):
        """Return the display label for a given field."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('label', field_name)
        return field_name

    def get_field_type(self, field_name):
        """Return the type for a given field (e.g., 'slider', 'text')."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('type', 'text')
        return 'text'

    def get_field_default(self, field_name):
        """Return the default value for a given field."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('default', '')
        return ''

    def get_field_options(self, field_name):
        """Return options for a given field (for dropdowns, etc.), or None."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('options')
        return None

    def handle_button_action(self, action_name):
        """
        Handle button actions from the GUI.
        
        Args:
            action_name (str): Name of the button action to handle
            
        Note: This method is called by the GUI when a button in the module's
        configuration is clicked. Currently supports 'reset' action.
        """
        if action_name == "reset":
            self.log_message("🔄 Reset button pressed - restarting OSC server")
            # Restart the server to clear any issues
            if self.is_running:
                self.stop()
                time.sleep(0.1)  # Brief delay to ensure cleanup
                self.start()
                self.log_message("✅ OSC server restarted after reset")
            else:
                self.log_message("⚠️ Cannot reset - server not running")
        else:
            self.log_message(f"⚠️ Unknown button action: {action_name}")
