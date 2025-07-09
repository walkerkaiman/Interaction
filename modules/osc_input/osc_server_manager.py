import socket
import threading
import time
from pythonosc import dispatcher, osc_server
from collections import defaultdict

class OSCServerManager:
    """Manages shared OSC servers for multiple interactions"""
    
    def __init__(self, log_callback=print):
        self.servers = {}  # port -> server instance
        self.dispatchers = {}  # port -> dispatcher instance
        self.server_threads = {}  # port -> thread instance
        self.callbacks = defaultdict(lambda: defaultdict(list))  # port -> {address -> [callbacks]}
        self.running = {}  # port -> running status
        self.log = log_callback
        
    def register_callback(self, port, address, callback):
        """Register a callback for a specific port and address"""
        port = int(port)
        
        self.log(f"🔧 Registering callback for port {port}, address '{address}'")
        
        # Add callback to our registry (support multiple callbacks per address)
        self.callbacks[port][address].append(callback)
        
        # Create or update dispatcher for this port
        if port not in self.dispatchers:
            self.dispatchers[port] = dispatcher.Dispatcher()
        
        # Always create a new handler for this address to ensure it's current
        # Remove any existing handler first
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
    
    def unregister_callback(self, port, address, callback=None):
        """Unregister a callback for a specific port and address"""
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
    
    def _create_message_handler(self, port, address):
        """Create a message handler that calls only callbacks for this specific address"""
        def message_handler(osc_address, *args):
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
    
    def _check_port_available(self, port):
        """Check if a specific port is available"""
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
    
    def _start_server(self, port):
        """Start an OSC server on the specified port"""
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
            ip = "0.0.0.0"
            server = osc_server.ThreadingOSCUDPServer((ip, port), self.dispatchers[port])
            
            self.servers[port] = server
            self.running[port] = True
            
            # Start server in a thread
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            self.server_threads[port] = server_thread
            
            self.log(f"✅ Shared OSC Server started at {ip}:{port}")
            self.log(f"📡 Listening for addresses: {list(self.callbacks[port].keys())}")
            
        except Exception as e:
            self.log(f"❌ Failed to start OSC Server on port {port}: {e}")
            self.running[port] = False
    
    def _stop_server(self, port):
        """Stop an OSC server on the specified port"""
        if port in self.servers:
            try:
                self.log(f"🛑 Stopping OSC server on port {port}")
                self.servers[port].shutdown()
                self.servers[port].server_close()
                
                # Wait for thread to finish
                if port in self.server_threads and self.server_threads[port].is_alive():
                    self.server_threads[port].join(timeout=2.0)
                
                del self.servers[port]
                del self.server_threads[port]
                self.running[port] = False
                
                self.log(f"✅ OSC server on port {port} stopped")
                
            except Exception as e:
                self.log(f"⚠️ Error stopping OSC server on port {port}: {e}")
    
    def get_active_ports(self):
        """Get list of active ports"""
        return list(self.servers.keys())
    
    def get_addresses_for_port(self, port):
        """Get list of addresses being listened to on a specific port"""
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
        """Shutdown all OSC servers"""
        ports = list(self.servers.keys())
        for port in ports:
            self._stop_server(port)

# Global instance
osc_manager = OSCServerManager() 