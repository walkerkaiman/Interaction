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
from modules.osc_input.osc_server_manager import OSCServerManager

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
        
        self._event_callback = None  # Add this line to store the callback
        
        # Log initialization
        self.log_message(f"OSC Input initialized - Port: {self.port}, Address: {self.address}")
    
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
            self.log_message(f"✅ OSC server started on port {self.port}, listening for '{self.address}'")
            
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
    
    def set_event_callback(self, callback):
        """
        Set a callback to be called when an OSC event is received.
        """
        self._event_callback = callback
    
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
            # Create event data from OSC message
            event_data = {
                "address": address,
                "args": list(args),
                "timestamp": time.time()
            }
            
            # Add trigger value (first argument) for compatibility
            if args:
                event_data["trigger"] = args[0]
            else:
                event_data["trigger"] = 1.0  # Default trigger value
            
            # Log the received message
            self.log_message(f"📨 OSC message received: {address} {args}")
            
            # Call the event callback if set
            if self._event_callback:
                self._event_callback(event_data)
            
            # Emit the event to connected output modules
            self.emit_event(event_data)
            
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
            self._handle_osc_message(self.address, 0.75)
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
