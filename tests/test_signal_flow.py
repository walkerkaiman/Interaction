import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from unittest.mock import MagicMock
from modules.time_input_trigger.clock_input import TimeInputModule
from modules.audio_output.audio_output import AudioOutputModule
from modules.module_base import ModuleBase
from message_router import EventRouter

class DummyOutputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=None, strategy=None):
        super().__init__(config, manifest, log_callback, strategy)
        self.received_events = []
    def handle_event(self, data):
        self.received_events.append(data)

@pytest.fixture
def event_router():
    # Use a fresh EventRouter for each test
    return EventRouter()

def test_input_to_output_signal_flow(event_router):
    # Setup input and output modules
    input_manifest = {"name": "TimeInputModule"}
    output_manifest = {"name": "DummyOutputModule"}
    input_module = TimeInputModule({"target_time": "12:00:00"}, input_manifest)
    output_module = DummyOutputModule({}, output_manifest)
    # Register output module to listen for events
    event_router.subscribe('module_event', lambda event, settings=None: output_module.handle_event(event['data']))
    # Patch input module to use this router
    input_module.event_router = event_router
    # Emit a test event
    test_event = {"current_time": "12:00:01", "countdown": "00:00:01", "target_time": "12:00:00"}
    input_module.emit_event(test_event)
    # Check that output module received the event
    assert any(e.get("current_time") == "12:00:01" for e in output_module.received_events) 