"""
Message Router - Event Routing System for Interaction Modules

This file implements the message routing system that connects input modules to
output modules in the Interaction framework. The message router acts as the
central nervous system of the application, handling all communication between
modules.

Key Responsibilities:
1. Connect input modules to output modules
2. Route events from input modules to output modules
3. Manage module lifecycle and cleanup
4. Provide event filtering and transformation
5. Handle error recovery and logging

The message router uses a simple callback-based system where:
- Input modules register event callbacks with output modules
- When an input module emits an event, the router calls all registered callbacks
- Output modules receive events through their handle_event method
- The router manages the connection lifecycle and cleanup

Author: Interaction Framework Team
License: MIT
"""

import threading
from typing import Dict, List, Any, Callable, Optional, Tuple
import hashlib

class EventRouter:
    """
    Central event routing system for modules, GUI, and system events.
    Supports state tracking, settings-based routing, event subscription/publication,
    runtime reconfiguration, and debugging/logging hooks.
    """
    def __init__(self):
        self.connections = {}  # {input_settings_key: [output_modules]}
        self.state_subscribers = []  # [(module, callback)]
        self.event_subscribers = {}  # {event_type: [(callback, filter)]}
        self.lock = threading.Lock()
        self.module_states = {}  # {module_id: state}
        self.debug_log = []  # [(event_type, data, meta)]

    def _settings_key(self, settings: dict) -> str:
        # Create a hashable key from settings dict for grouping
        return hashlib.sha256(str(sorted(settings.items())).encode()).hexdigest() if settings else "default"

    def connect_modules(self, input_module, output_module, settings: Optional[dict]=None):
        # Use settings key for grouping outputs by input settings
        key = self._settings_key(settings or getattr(input_module, 'config', {}))
        with self.lock:
            if key not in self.connections:
                self.connections[key] = []
            if output_module not in self.connections[key]:
                self.connections[key].append(output_module)
                input_module.add_event_callback(output_module.handle_event)
                self._log_debug('connect', {'input': input_module, 'output': output_module, 'settings': settings})
        return True

    def disconnect_modules(self, input_module, output_module, settings: Optional[dict]=None):
        key = self._settings_key(settings or getattr(input_module, 'config', {}))
        with self.lock:
            if key in self.connections and output_module in self.connections[key]:
                self.connections[key].remove(output_module)
                input_module.remove_event_callback(output_module.handle_event)
                self._log_debug('disconnect', {'input': input_module, 'output': output_module, 'settings': settings})
                if not self.connections[key]:
                    del self.connections[key]

    def subscribe(self, event_type: str, callback: Callable, filter: Optional[Callable]=None):
        with self.lock:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            self.event_subscribers[event_type].append((callback, filter))

    def unsubscribe(self, event_type: str, callback: Callable):
        with self.lock:
            if event_type in self.event_subscribers:
                self.event_subscribers[event_type] = [
                    (cb, f) for (cb, f) in self.event_subscribers[event_type] if cb != callback
                ]

    def publish(self, event_type: str, data: Any, settings: Optional[dict]=None):
        # Publish an event to all subscribers (optionally filtered by settings)
        with self.lock:
            for cb, filt in self.event_subscribers.get(event_type, []):
                if filt is None or filt(data, settings):
                    cb(data)
            self._log_debug('publish', {'event_type': event_type, 'data': data, 'settings': settings})

    def register_state_subscriber(self, module, callback: Callable):
        with self.lock:
            self.state_subscribers.append((module, callback))

    def emit_state_change(self, module, new_state: str):
        module_id = id(module)
        with self.lock:
            self.module_states[module_id] = new_state
            for m, cb in self.state_subscribers:
                if m is None or m == module:
                    cb(module, new_state)
            self._log_debug('state_change', {'module': module, 'state': new_state})

    def get_module_state(self, module) -> Optional[str]:
        return self.module_states.get(id(module))

    def get_all_states(self) -> Dict[int, str]:
        return dict(self.module_states)

    def get_connections(self):
        with self.lock:
            return {k: list(v) for k, v in self.connections.items()}

    def reconfigure_connection(self, input_module, output_module, old_settings: dict, new_settings: dict):
        self.disconnect_modules(input_module, output_module, old_settings)
        self.connect_modules(input_module, output_module, new_settings)
        self._log_debug('reconfigure', {'input': input_module, 'output': output_module, 'old': old_settings, 'new': new_settings})

    def clear_all_connections(self):
        with self.lock:
            for key, outputs in self.connections.items():
                for output in outputs:
                    # No direct reference to input_module, so this is a best-effort cleanup
                    pass
            self.connections.clear()
            self._log_debug('clear_all', {})

    def _log_debug(self, event_type, meta):
        self.debug_log.append((event_type, meta))
        # Optionally, print or send to GUI for live debugging

# For backward compatibility
MessageRouter = EventRouter
