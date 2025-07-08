import json
import os
from abc import ABC, abstractmethod


class BaseModule(ABC):
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

    def log_message(self, msg: str):
        name = self.manifest.get("name", "UnnamedModule")
        self.log(f"[{name}] {msg}")

    def set_event_callback(self, callback_fn):
        """
        Optional. Input modules can override this method to accept
        a function to call when an event is triggered.
        """
        pass

    def handle_event(self, data=None):
        """
        Optional. Output modules can override this method to respond
        to events triggered by input modules.
        """
        pass
