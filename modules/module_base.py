"""
Module Base Class - Foundation for All Interaction Modules

This file defines the ModuleBase class, which serves as the foundation for all
input and output modules in the Interaction framework. It provides common
functionality that all modules need:

1. Configuration Management: Loading, saving, and updating module settings
2. Event System: Emitting events to connected modules and handling incoming events
3. Logging: Standardized logging interface for all modules
4. Lifecycle Management: Start/stop methods for resource management
5. Manifest Integration: Loading and validating module metadata

All custom modules must inherit from ModuleBase and implement the required methods.
This ensures consistency across the module ecosystem and provides a unified interface
for the message router and GUI.

Author: Interaction Framework Team
License: MIT
"""

import json
import os
from typing import Dict, Any, Callable, Optional
from message_router import EventRouter
from abc import ABC, abstractmethod
import uuid
import time

class ModuleStrategy(ABC):
    @abstractmethod
    def process_event(self, event: Dict) -> None:
        pass

    @abstractmethod
    def configure(self, config: Dict) -> None:
        pass

class TriggerStrategy(ModuleStrategy):
    """
    TriggerStrategy - Standardized trigger event handler for output modules.

    This strategy enables any output module (audio, OSC, DMX, etc.) to respond to trigger events in a unified way.
    When a trigger event is received, the strategy will:
      - Call the module's `on_trigger(event)` method if it exists.
      - Print debug information if no handler is implemented.

    To add a new triggerable output module:
      1. Implement an `on_trigger(self, event)` method in your module class.
      2. The system will automatically call this method when the module is triggered (e.g., by a manual button press in the GUI).
      3. No changes to the strategy or core logic are needed—just add the method to your new module.

    This design ensures modularity, extensibility, and ease of maintenance for all triggerable outputs.
    """
    def process_event(self, event: Dict, module=None) -> None:
        """
        Process a trigger event for the given module.

        Args:
            event (Dict): The event data (e.g., {'data': 'manual_trigger', ...})
            module: The output module instance to trigger (must implement on_trigger)

        If the module implements `on_trigger`, it will be called with the event.
        Otherwise, a debug message is printed.
        """
        print(f"[AUDIO DEBUG] TriggerStrategy.process_event called with event: {event}, module: {module}")
        if module is not None:
            # Call a module-specific on_trigger method if it exists
            if hasattr(module, 'on_trigger') and callable(getattr(module, 'on_trigger')):
                print(f"[AUDIO DEBUG] TriggerStrategy: calling {module.__class__.__name__}.on_trigger")
                module.on_trigger(event)
            else:
                print(f"[AUDIO DEBUG] TriggerStrategy: No trigger handler implemented for {module.__class__.__name__}")
    def configure(self, config: Dict) -> None:
        # Configure trigger-based module (to be implemented in concrete modules)
        pass

class StreamingStrategy(ModuleStrategy):
    def process_event(self, event: Dict) -> None:
        # Handle streaming events (to be implemented in concrete modules)
        pass
    def configure(self, config: Dict) -> None:
        # Configure streaming module (to be implemented in concrete modules)
        pass

class ModuleState(ABC):
    @abstractmethod
    def start(self, context: 'ModuleBase') -> None:
        pass
    @abstractmethod
    def stop(self, context: 'ModuleBase') -> None:
        pass
    @abstractmethod
    def handle_event(self, context: 'ModuleBase', event: Dict) -> None:
        pass

class InitializedState(ModuleState):
    def start(self, context: 'ModuleBase') -> None:
        context.auto_configure()
        context.set_state('starting')
        context.log_message(f"Starting {context.manifest.get('name', 'Unknown Module')}")
        context.set_state('ready')
        context.set_state_obj(RunningState())
    def stop(self, context: 'ModuleBase') -> None:
        context.log_message("Cannot stop: Module not started.")
    def handle_event(self, context: 'ModuleBase', event: Dict) -> None:
        context.log_message("Warning: Module not started. Event ignored.")

class RunningState(ModuleState):
    def start(self, context: 'ModuleBase') -> None:
        context.log_message("Module already running.")
    def stop(self, context: 'ModuleBase') -> None:
        context.set_state('stopping')
        context.log_message(f"Stopping {context.manifest.get('name', 'Unknown Module')}")
        context.set_state('stopped')
        context.set_state_obj(StoppedState())
    def handle_event(self, context: 'ModuleBase', event: Dict) -> None:
        if context.strategy:
            context.strategy.process_event(event)
        else:
            context.log_message(f"Received event: {event}")

class StoppedState(ModuleState):
    def start(self, context: 'ModuleBase') -> None:
        context.log_message("Restarting module...")
        context.set_state_obj(InitializedState())
        context.start()
    def stop(self, context: 'ModuleBase') -> None:
        context.log_message("Module already stopped.")
    def handle_event(self, context: 'ModuleBase', event: Dict) -> None:
        context.log_message("Warning: Module stopped. Event ignored.")

class ModuleBase:
    """
    Base class for all Interaction modules (input and output), now event-driven and stateful.
    Handles config, manifest, state, event emission, and lifecycle via EventRouter.
    """
    event_router = EventRouter()  # Shared router for all modules

    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], log_callback: Optional[Callable] = None, strategy: Optional[ModuleStrategy] = None):
        self.config = config or {}
        self.manifest = manifest or {}
        self.log_callback = log_callback if log_callback is not None else (lambda *args, **kwargs: None)
        self.state = 'created'
        self._event_callbacks = []  # For backward compatibility
        self.strategy = strategy
        self.state_obj: ModuleState = InitializedState()
        self.event_router.emit_state_change(self, self.state)
        self.log_message(f"Initializing {self.manifest.get('name', 'Unknown Module')}")
        self.instance_id = str(uuid.uuid4())  # Unique ID for every module instance
        self.module_id: Optional[str] = None  # Ensure module_id always exists

    def set_state(self, new_state: str):
        self.state = new_state
        self.event_router.emit_state_change(self, new_state)
        self.log_message(f"State changed to {new_state}")

    def configure(self, config: Optional[Dict[str, Any]] = None):
        if self.strategy:
            self.strategy.configure(config or self.config)
        else:
            if config is not None:
                self.config = config
            self.set_state('configured')
            self.log_message(f"Configured with: {self.config}")

    def start(self):
        self.state_obj.start(self)

    def stop(self):
        self.state_obj.stop(self)
        self.wait_for_stop()
        self.log_message(f"🛑 ModuleBase stopped (instance {self.instance_id})")

    def wait_for_stop(self):
        """
        Subclasses should override this if they have background threads/tasks to join/cancel.
        This method is called after stop() to ensure cleanup before a new instance is started.
        """
        pass

    def cleanup(self):
        self.set_state('cleaning_up')
        self.log_message(f"Cleaning up {self.manifest.get('name', 'Unknown Module')}")
        self.set_state('cleaned_up')

    def emit_event(self, data: Dict[str, Any]):
        data = dict(data)  # Copy to avoid mutating caller's dict
        data['instance_id'] = self.instance_id  # Always include instance_id
        self.log_message(f"Emitting event: {data}")
        self.event_router.publish('module_event', {'module': self, 'data': data}, settings=self.config)
        # For backward compatibility, call direct callbacks
        for callback in self._event_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.log_message(f"Error in event callback: {e}")

    def handle_event(self, data: Dict[str, Any]):
        self.state_obj.handle_event(self, data)
        # Subclasses override for custom behavior

    def add_event_callback(self, callback: Callable):
        # For backward compatibility; new code should use EventRouter
        if callback is not None:
            self._event_callbacks.append(callback)

    def remove_event_callback(self, callback: Callable):
        if callback is not None and callback in self._event_callbacks:
            self._event_callbacks.remove(callback)

    def log_message(self, message: str):
        # Suppress 'Emitting event:' messages from terminal, but always broadcast to frontend
        if not message.startswith("Emitting event:"):
            if '❌' in message or '🛑' in message:
                print(message)
            elif not (message.startswith("Emitting event:")):
                print(message)
        # Broadcast console logs to frontend via WebSocket
        try:
            from main import broadcast_ws_event
            broadcast_ws_event({
              "type": "console_log",
                "message": message,
                "module": self.manifest.get('name', 'Unknown Module'),
               "timestamp": time.time()
            })
        except ImportError:
            # If main module is not available, just continue
            pass
        self.event_router._log_debug('log', {'module': self, 'msg': message})

    def update_config(self, new_config: Dict[str, Any]):
        old_config = self.config.copy()
        self.config = new_config
        self.log_message(f"Configuration updated: {old_config} -> {new_config}")
        # Call the hook for each changed field
        for k, v in new_config.items():
            if old_config.get(k) != v:
                self.on_config_field_changed(k, old_config.get(k), v)
        self.set_state('configured')

    def on_config_field_changed(self, field_name, old_value, new_value):
        # By default, do nothing. Subclasses can override for dynamic config changes.
        pass

    def get_config(self) -> Dict[str, Any]:
        return self.config.copy()

    def get_manifest(self) -> Dict[str, Any]:
        return self.manifest.copy()

    def validate_config(self, config: Dict[str, Any]) -> bool:
        if not self.manifest or 'config_schema' not in self.manifest:
            return True
        schema = self.manifest['config_schema']
        for field_name, field_info in schema.items():
            if field_info.get('required', False) and field_name not in config:
                self.log_message(f"Missing required field: {field_name}")
                return False
            if field_name in config and 'type' in field_info:
                expected_type = field_info['type']
                actual_value = config[field_name]
                if expected_type == 'number' and not isinstance(actual_value, (int, float)):
                    self.log_message(f"Field {field_name} must be a number")
                    return False
                elif expected_type == 'string' and not isinstance(actual_value, str):
                    self.log_message(f"Field {field_name} must be a string")
                    return False
                elif expected_type == 'boolean' and not isinstance(actual_value, bool):
                    self.log_message(f"Field {field_name} must be a boolean")
                    return False
        return True

    def auto_configure(self):
        pass

    def set_state_obj(self, new_state_obj: ModuleState):
        self.state_obj = new_state_obj
