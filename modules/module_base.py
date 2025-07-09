import json
import os
from abc import ABC, abstractmethod


class ModuleBase(ABC):
    def __init__(self, config: dict, manifest: dict, log_callback=print):
        """
        config: instance-specific settings for this module (from interaction_X.json)
        manifest: static metadata describing the module (from manifest.json)
        log_callback: function to send log messages to the GUI
        """
        self.config = config
        self.manifest = manifest
        self.log = log_callback
        self.running = False
        self.event_callback = None

    @abstractmethod
    def start(self):
        """Begin the module's activity. Set up servers, threads, etc."""
        pass

    @abstractmethod
    def stop(self):
        """Stop and clean up the module."""
        pass

    def update_config(self, new_config: dict):
        """
        Called by the GUI when the user changes config values.
        Override this method if the module needs to react to changes.
        """
        self.config = new_config
        self.log_message("Configuration updated.")

    def log_message(self, msg: str, level="show_mode"):
        """
        Log a message with the specified level.
        level: "no_log", "output_trigger", "show_mode", "verbose"
        """
        name = self.manifest.get("name", "UnnamedModule")
        
        # Handle different log levels
        if hasattr(self.log, level):
            # If the logger supports the new system, use the appropriate method
            getattr(self.log, level)(f"[{name}] {msg}")
        else:
            # Fallback to the old system
            self.log(f"[{name}] {msg}")

    def set_event_callback(self, callback_fn):
        """
        Optional. Input modules can override this method to accept
        a function to call when an event is triggered.
        """
        self.event_callback = callback_fn

    def handle_event(self, event_data):
        """
        Optional. Output modules can override this method to respond
        to events triggered by input modules.
        """
        if self.event_callback:
            self.event_callback(event_data)
            
    def emit_event(self, event_data):
        if self.event_callback:
            self.event_callback(event_data)
