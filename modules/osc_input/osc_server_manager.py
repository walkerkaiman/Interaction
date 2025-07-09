"""
OSC Server Manager - Shared OSC Server Management System

This module implements a shared OSC server management system that allows multiple
OSC input modules to listen on the same UDP port but different OSC addresses
without conflicts. It provides centralized server management, callback routing,
and resource cleanup.

Key Features:
1. Shared UDP servers for multiple OSC input modules
2. Address-specific callback routing
3. Automatic server lifecycle management
4. Thread-safe operation
5. Port conflict detection and handling
6. Graceful shutdown and cleanup

The server manager uses a dispatcher-based system where:
- Each port has one UDP server instance
- Multiple OSC addresses can be registered on the same port
- Each address can have multiple callbacks
- Messages are routed to the correct callbacks based on address
- Servers are automatically started/stopped based on usage

Author: Interaction Framework Team
License: MIT
"""

import socket
import threading
import time
from pythonosc import dispatcher, osc_server
from collections import defaultdict
from typing import Dict, List, Callable, Any, Optional

class OSCServerManager:
    """
    Shared OSC server manager for multiple OSC input modules.
    
    This class manages shared OSC servers that allow multiple OSC input modules
    to listen on the same UDP port but different OSC addresses without conflicts.
    It provides centralized server management, callback routing, and resource cleanup.
    
    The manager uses a hierarchical structure:
    - Port -> Server instance (one UDP server per port)
    - Port -> Dispatcher instance (one dispatcher per port)
    - Port -> Address -> List of callbacks (multiple callbacks per address)
    
    Key Features:
    - Shared UDP servers for multiple modules
    - Address-specific callback routing
    - Automatic server lifecycle management
    - Thread-safe operation with locks
    - Port conflict detection and handling
    - Graceful shutdown and cleanup
    
    Attributes:
        servers (Dict): Port -> server instance mapping
        dispatchers (Dict): Port -> dispatcher instance mapping
        server_threads (Dict): Port -> server thread mapping
        callbacks (Dict): Port -> {address -> [callbacks]} mapping
        running (Dict): Port -> running status mapping
        log (Callable): Logging function
    """
    
    def __init__(self, log_callback=print):
        """
        Initialize the OSC server manager.
        
        Args:
            log_callback (Callable): Function to call for logging
            
        Note: The manager starts with no servers running. Servers are
        created automatically when the first callback is registered.
        """
        # Server instances: port -> server object
        self.servers = {}
        
        # OSC dispatchers: port -> dispatcher object
        self.dispatchers = {}
        
        # Server threads: port -> thread object
        self.server_threads = {}
        
        # Callback registry: port -> {address -> [callbacks]}
        # Uses defaultdict to automatically create empty lists
        self.callbacks = defaultdict(lambda: defaultdict(list))
        
        # Running status: port -> boolean
        self.running = {}
        
        # Logging function
        self.log = log_callback
        
        self.log("🔧 OSC Server Manager initialized")
    
    def register_callback(self, port: int, address: str, callback: Callable):
        """
        Register a callback for a specific port and OSC address.
        
        This method registers a callback function to be called when an OSC
        message is received on the specified port and address. Multiple
        callbacks can be registered for the same address, and they will
        all be called when a message is received.
        
        Args:
            port (int): UDP port to listen on
            address (str): OSC address pattern to match
            callback (Callable): Function to call when message is received
            
        Note: The server manager will automatically start a server on the
        specified port if one doesn't already exist. The callback will be
        called with the OSC message data when a matching message is received.
        
        Example:
            manager = OSCServerManager()
            manager.register_callback(8000, "/trigger", my_callback)
            # Now my_callback will be called when /trigger messages are received on port 8000
        """
        port = int(port)
        
        self.log(f"🔧 Registering callback for port {port}, address '{address}'")
        
        # Add callback to our registry (support multiple callbacks per address)
        self.callbacks[port][address].append(callback)
        
        # Create or update dispatcher for this port
        if port not in self.dispatchers:
            self.dispatchers[port] = dispatcher.Dispatcher()
        
        # Always create a new handler for this address to ensure it's current
        # Remove any existing handler first to avoid conflicts
        if self.dispatchers[port]._map.get(address):
            self.log(f"📡 Updating existing message handler for address '{address}' on port {port}")
            # Remove the old handler
            self.dispatchers[port]._map.pop(address, None)
            self.log(f"🗑️ Removed old handler for '{address}' from dispatcher")
        else:
            self.log(f"📡 Creating new message handler for address '{address}' on port {port}")
        
        # Map the address to our internal handler
        self.dispatchers[port].map(address, self._create_message_handler(port, address))
        self.log(f"✅ Mapped address '{address}' to handler on port {port}")
        
        # Debug: show all current handlers for this port
        current_handlers = list(self.dispatchers[port]._map.keys())
        self.log(f"📋 Current handlers on port {port}: {current_handlers}")
        
        # Start server if not already running
        if port not in self.servers or not self.running.get(port, False):
            self._start_server(port)
    
    def unregister_callback(self, port: int, address: str, callback: Optional[Callable] = None):
        """
        Unregister a callback for a specific port and OSC address.
        
        This method removes a callback function from the registry. If no
        specific callback is provided, all callbacks for the address are removed.
        If no callbacks remain for a port, the server is automatically stopped.
        
        Args:
            port (int): UDP port to unregister from
            address (str): OSC address pattern to unregister from
            callback (Callable, optional): Specific callback to remove
            
        Note: This method is called automatically when OSC input modules are
        stopped or reconfigured. It ensures proper cleanup of resources.
        """
        port = int(port)
        
        self.log(f"🔧 Unregistering callback for port {port}, address '{address}'")
        
        if port in self.callbacks and address in self.callbacks[port]:
            if callback is None:
                # Remove all callbacks for this address
                callback_count = len(self.callbacks[port][address])
                del self.callbacks[port][address]
                self.log(f"🗑️ Removed all {callback_count} callback(s) for address '{address}'")
            else:
                # Remove specific callback
                if callback in self.callbacks[port][address]:
                    self.callbacks[port][address].remove(callback)
                    self.log(f"🗑️ Removed specific callback for address '{address}'")
                if not self.callbacks[port][address]:
                    del self.callbacks[port][address]
                    self.log(f"🗑️ Removed empty callback list for address '{address}'")
            
            # Remove the handler from the dispatcher if no more callbacks for this address
            if address not in self.callbacks[port]:
                if port in self.dispatchers and address in self.dispatchers[port]._map:
                    self.dispatchers[port]._map.pop(address, None)
                    self.log(f"🗑️ Removed handler for address '{address}' from dispatcher")
                else:
                    self.log(f"⚠️ Handler for '{address}' not found in dispatcher (already removed?)")
                
                # Debug: show remaining handlers
                if port in self.dispatchers:
                    remaining_handlers = list(self.dispatchers[port]._map.keys())
                    self.log(f"📋 Remaining handlers on port {port}: {remaining_handlers}")
            
            # If no more callbacks for this port, stop the server
            if not self.callbacks[port]:
                self.log(f"🛑 No more callbacks for port {port}, stopping server")
                self._stop_server(port)
            else:
                self.log(f"📡 Remaining addresses on port {port}: {list(self.callbacks[port].keys())}")
        else:
            self.log(f"⚠️ No callbacks found to unregister for port {port}, address '{address}'")
    
    def _create_message_handler(self, port: int, address: str) -> Callable:
        """
        Create a message handler that calls only callbacks for this specific address.
        
        This method creates a specialized message handler that ensures OSC messages
        are only routed to callbacks registered for the specific address that
        received the message. This prevents cross-talk between different addresses
        on the same port.
        
        Args:
            port (int): UDP port the handler is for
            address (str): OSC address the handler is for
            
        Returns:
            Callable: Message handler function
            
        Note: The returned handler function is registered with the OSC dispatcher
        and is called automatically when OSC messages are received.
        """
        def message_handler(osc_address: str, *args):
            self.log(f"📥 OSC message received on port {port}, address '{osc_address}' (handler for '{address}')")
            
            # Verify that the message address matches our handler address
            if osc_address != address:
                self.log(f"⚠️ Address mismatch! Message address '{osc_address}' != handler address '{address}' - IGNORING")
                return
            
            # Only call callbacks for this specific address
            if port in self.callbacks and address in self.callbacks[port]:
                data = {"address": osc_address, "args": args}
                callback_count = len(self.callbacks[port][address])
                self.log(f"🎯 Calling {callback_count} callback(s) for address '{address}'")
                
                # Call only the callbacks registered for this specific address
                for i, callback in enumerate(self.callbacks[port][address]):
                    try:
                        self.log(f"📞 Executing callback {i+1}/{callback_count} for '{address}'")
                        callback(data)
                    except Exception as e:
                        self.log(f"⚠️ Error in OSC callback for {address}: {e}")
            else:
                self.log(f"⚠️ No callbacks found for address '{address}' on port {port}")
        
        return message_handler
    
    def _check_port_available(self, port: int) -> bool:
        """
        Check if a specific port is available for binding.
        
        This method checks if a port can be bound to by attempting to create
        a test socket. It also considers a port available if we already have
        a server running on it.
        
        Args:
            port (int): Port number to check
            
        Returns:
            bool: True if port is available, False otherwise
            
        Note: This method is used to detect port conflicts before starting
        a new server. It helps prevent startup failures due to port conflicts.
        """
        # If we already have a server running on this port, consider it available
        if port in self.servers and self.running.get(port, False):
            return True
            
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as test_socket:
                test_socket.bind(('0.0.0.0', port))
                test_socket.close()
                return True
        except OSError:
            return False
    
    def _start_server(self, port: int):
        """
        Start an OSC server on the specified port.
        
        This method creates and starts a UDP server on the specified port.
        The server runs in a separate thread to avoid blocking the main
        application. The server uses the dispatcher for this port to route
        incoming messages to the appropriate callbacks.
        
        Args:
            port (int): Port number to start server on
            
        Note: This method handles port conflicts, server restart, and
        thread management. It's called automatically when the first
        callback is registered for a port.
        """
        if port in self.servers and self.running.get(port, False):
            self.log(f"✅ Server already running on port {port}")
            return  # Already running
        
        # Stop any existing server on this port first
        if port in self.servers:
            self.log(f"🔄 Stopping existing server on port {port} before restarting")
            self._stop_server(port)
        
        if not self._check_port_available(port):
            self.log(f"❌ Port {port} is not available")
            return
        
        try:
            ip = "0.0.0.0"  # Listen on all interfaces
            server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatchers[port])
            
            self.servers[port] = server
            self.running[port] = True
            
            # Start server in a daemon thread (will be terminated when main program exits)
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            self.server_threads[port] = server_thread
            
            self.log(f"✅ Shared OSC Server started at {ip}:{port}")
            self.log(f"📡 Listening for addresses: {list(self.callbacks[port].keys())}")
            
        except Exception as e:
            self.log(f"❌ Failed to start OSC Server on port {port}: {e}")
            self.running[port] = False
    
    def _stop_server(self, port: int):
        """
        Stop an OSC server on the specified port.
        
        This method gracefully shuts down a UDP server and cleans up all
        associated resources. It waits for the server thread to finish
        before returning.
        
        Args:
            port (int): Port number to stop server on
            
        Note: This method is called automatically when all callbacks for
        a port are unregistered, or when the application is shutting down.
        """
        if port in self.servers:
            try:
                self.log(f"🛑 Stopping OSC server on port {port}")
                self.servers[port].shutdown()
                self.servers[port].server_close()
                
                # Wait for thread to finish (with timeout to prevent hanging)
                if port in self.server_threads and self.server_threads[port].is_alive():
                    self.server_threads[port].join(timeout=2.0)
                
                del self.servers[port]
                del self.server_threads[port]
                self.running[port] = False
                
                self.log(f"✅ OSC server on port {port} stopped")
                
            except Exception as e:
                self.log(f"⚠️ Error stopping OSC server on port {port}: {e}")
    
    def get_active_ports(self) -> List[int]:
        """
        Get list of active ports with running servers.
        
        Returns:
            List[int]: List of port numbers with active servers
            
        Note: This method is useful for debugging and monitoring
        which ports are currently being used.
        """
        return list(self.servers.keys())
    
    def get_addresses_for_port(self, port: int) -> List[str]:
        """
        Get list of addresses being listened to on a specific port.
        
        Args:
            port (int): Port number to check
            
        Returns:
            List[str]: List of OSC addresses being listened to on the port
            
        Note: This method is useful for debugging and monitoring
        which addresses are registered on each port.
        """
        port = int(port)
        return list(self.callbacks.get(port, {}).keys())
    
    def get_status(self):
        """Get a status summary of active OSC servers"""
        if not self.servers:
            return "No active servers"
        
        status_parts = []
        for port in self.servers.keys():
            addresses = self.get_addresses_for_port(port)
            status_parts.append(f"Port {port}: {', '.join(addresses)}")
        
        return " | ".join(status_parts)
    
    def shutdown_all(self):
        """
        Shutdown all OSC servers and clean up resources.
        
        This method stops all running servers and cleans up all resources.
        It's typically called when the application is shutting down to
        ensure proper cleanup of network resources and threads.
        
        Note: This method should be called before the application exits
        to prevent resource leaks and ensure clean shutdown.
        """
        self.log("🛑 Shutting down all OSC servers")
        
        # Stop all servers
        for port in list(self.servers.keys()):
            self._stop_server(port)
        
        # Clear all callbacks
        self.callbacks.clear()
        
        self.log("✅ All OSC servers shut down")

# Global instance
osc_manager = OSCServerManager() 