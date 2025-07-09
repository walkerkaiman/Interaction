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

class ModuleBase:
    """
    Base class for all Interaction modules (input and output).
    
    This class provides the foundation that all modules build upon. It handles
    common functionality like configuration management, event emission, logging,
    and lifecycle management. Modules that inherit from this class get all this
    functionality automatically.
    
    Key Features:
    - Configuration loading and saving
    - Event emission to connected modules
    - Standardized logging interface
    - Lifecycle management (start/stop)
    - Manifest validation and loading
    
    Attributes:
        config (Dict[str, Any]): Module configuration dictionary
        manifest (Dict[str, Any]): Module manifest dictionary
        log_callback (Callable): Function to call for logging
        _event_callbacks (List[Callable]): List of callback functions for events
    """
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], 
                 log_callback: Callable = print):
        """
        Initialize the module with configuration and manifest.
        
        Args:
            config (Dict[str, Any]): Module configuration dictionary
            manifest (Dict[str, Any]): Module manifest dictionary containing metadata
            log_callback (Callable): Function to call for logging (default: print)
            
        Note: The manifest contains metadata about the module including its name,
        type (input/output), description, and configuration schema. The config
        contains the actual settings for this specific instance of the module.
        """
        self.config = config or {}
        self.manifest = manifest or {}
        self.log_callback = log_callback
        self._event_callbacks = []
        
        # Log module initialization
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"Initializing {module_name}")
    
    def start(self):
        """
        Start the module's operation.
        
        This method should be overridden by subclasses to initialize any
        resources needed for the module to function (network connections,
        audio devices, sensors, etc.).
        
        The base implementation just logs that the module has started.
        Subclasses should call super().start() to maintain logging.
        
        Note: This method is called by the GUI when the module is activated.
        It's the responsibility of the module to handle any errors that occur
        during startup and log them appropriately.
        """
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"Starting {module_name}")
    
    def stop(self):
        """
        Stop the module's operation and clean up resources.
        
        This method should be overridden by subclasses to clean up any
        resources that were allocated during start() (close network connections,
        release audio devices, stop sensors, etc.).
        
        The base implementation just logs that the module has stopped.
        Subclasses should call super().stop() to maintain logging.
        
        Note: This method is called by the GUI when the module is deactivated
        or when the application is shutting down. It's critical that all
        resources are properly cleaned up to prevent memory leaks and
        resource contention.
        """
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"Stopping {module_name}")
    
    def emit_event(self, data: Dict[str, Any]):
        """
        Emit an event to all connected modules.
        
        This method is used by input modules to send events to output modules.
        The event data can contain any information that the output module needs
        to generate its response.
        
        Args:
            data (Dict[str, Any]): Event data dictionary containing the event information
            
        Note: The event system is the primary mechanism for communication between
        modules. Input modules emit events when they receive triggers, and output
        modules receive these events and generate responses. The message router
        handles the actual routing of events between modules.
        
        Example:
            # Emit a simple trigger event
            self.emit_event({"trigger": 0.75})
            
            # Emit a complex event with multiple fields
            self.emit_event({
                "address": "/trigger",
                "args": ["value"],
                "trigger": 0.75,
                "timestamp": time.time()
            })
        """
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"{module_name} emitting event: {data}")
        
        # Call all registered event callbacks
        for callback in self._event_callbacks:
            try:
                callback(data)
            except Exception as e:
                self.log_message(f"Error in event callback: {e}")
    
    def handle_event(self, data: Dict[str, Any]):
        """
        Handle an incoming event from another module.
        
        This method is called by the message router when an event is sent to
        this module. Output modules should override this method to process
        incoming events and generate their responses.
        
        Args:
            data (Dict[str, Any]): Event data dictionary containing the event information
            
        Note: This is the primary method that output modules use to receive
        events from input modules. The method should be overridden to implement
        the specific behavior of the output module (play audio, trigger video,
        control lighting, etc.).
        
        Example:
            def handle_event(self, data):
                trigger_value = data.get("trigger", 0)
                if trigger_value > 0.5:
                    self.play_audio()
        """
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"{module_name} received event: {data}")
    
    def add_event_callback(self, callback: Callable):
        """
        Add a callback function to be called when events are emitted.
        
        This method is used internally by the message router to connect
        modules together. When an input module emits an event, all registered
        callbacks are called with the event data.
        
        Args:
            callback (Callable): Function to call when events are emitted
            
        Note: This is part of the internal event routing system. Most modules
        don't need to call this method directly - it's handled by the message
        router when modules are connected.
        """
        if callback not in self._event_callbacks:
            self._event_callbacks.append(callback)
    
    def remove_event_callback(self, callback: Callable):
        """
        Remove a callback function from the event callback list.
        
        This method is used internally by the message router to disconnect
        modules. When a module is removed or reconfigured, its callbacks
        are removed to prevent memory leaks.
        
        Args:
            callback (Callable): Function to remove from the callback list
            
        Note: This is part of the internal event routing system. Most modules
        don't need to call this method directly - it's handled by the message
        router when modules are disconnected.
        """
        if callback in self._event_callbacks:
            self._event_callbacks.remove(callback)
    
    def log_message(self, message: str):
        """
        Log a message using the module's logging callback.
        
        This method provides a standardized way for modules to log messages.
        The messages are passed to the log_callback function that was provided
        during initialization, which typically displays them in the GUI.
        
        Args:
            message (str): Message to log
            
        Note: All modules should use this method for logging instead of print()
        or other logging methods. This ensures that messages are displayed
        consistently in the GUI and can be filtered by log level.
        """
        if self.log_callback:
            self.log_callback(message)
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update the module's configuration.
        
        This method is called by the GUI when the user changes module settings.
        The module should update its internal state based on the new configuration
        and restart if necessary.
        
        Args:
            new_config (Dict[str, Any]): New configuration dictionary
            
        Note: This method is called automatically by the GUI when configuration
        changes are made. Modules should override this method if they need to
        perform special handling when their configuration changes (e.g., restart
        network connections, reload audio files, etc.).
        """
        old_config = self.config.copy()
        self.config = new_config
        
        module_name = self.manifest.get('name', 'Unknown Module')
        self.log_message(f"{module_name} configuration updated")
        
        # If the module needs to restart to apply new configuration,
        # subclasses should override this method and implement their own
        # restart logic based on their specific needs
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current module configuration.
        
        Returns:
            Dict[str, Any]: Current configuration dictionary
            
        Note: This method is used by the GUI to display and edit module
        configuration. The returned dictionary should contain all the
        configuration values that the module uses.
        """
        return self.config.copy()
    
    def get_manifest(self) -> Dict[str, Any]:
        """
        Get the module's manifest information.
        
        Returns:
            Dict[str, Any]: Module manifest dictionary
            
        Note: The manifest contains metadata about the module including its
        name, type, description, and configuration schema. This information
        is used by the GUI to display module information and generate
        configuration forms.
        """
        return self.manifest.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate a configuration dictionary against the module's schema.
        
        This method checks if the provided configuration matches the schema
        defined in the module's manifest. It ensures that all required fields
        are present and have the correct types.
        
        Args:
            config (Dict[str, Any]): Configuration to validate
            
        Returns:
            bool: True if configuration is valid, False otherwise
            
        Note: This method is used by the GUI to validate configuration changes
        before applying them. Modules can override this method to implement
        custom validation logic beyond the basic schema validation.
        """
        if not self.manifest or 'config_schema' not in self.manifest:
            return True  # No schema defined, assume valid
        
        schema = self.manifest['config_schema']
        
        # Check that all required fields are present
        for field_name, field_info in schema.items():
            if field_info.get('required', False) and field_name not in config:
                self.log_message(f"Missing required field: {field_name}")
                return False
            
            # Check field type if specified
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
