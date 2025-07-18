import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import time
from unittest.mock import MagicMock, patch
from modules.time_input_trigger.clock_input import TimeInputModule
from modules.serial_input_streaming.serial_input import SerialInputModule
from modules.serial_input_trigger.serial_trigger import SerialTriggerModule

@pytest.mark.parametrize("ModuleClass, config, event_key", [
    (TimeInputModule, {"target_time": "12:00:00"}, "current_time"),
    (SerialInputModule, {"serial_port": "COM1", "baud_rate": 9600}, "value"),
    (SerialTriggerModule, {"serial_port": "COM1", "baud_rate": 9600, "logic_operator": ">", "threshold_value": 0.5}, "value"),
])
def test_event_emission(ModuleClass, config, event_key):
    manifest = {"name": ModuleClass.__name__}
    module = ModuleClass(config, manifest)
    events = []
    module.add_event_callback(lambda data: events.append(data))
    # Patch serial port for SerialInputModule and SerialTriggerModule
    if ModuleClass in (SerialInputModule, SerialTriggerModule):
        module._open_serial = MagicMock(return_value=True)
        module.serial_conn = MagicMock()
        module.serial_conn.in_waiting = 1
        module.serial_conn.readline = MagicMock(return_value=b"1.0\n")
        if ModuleClass is SerialTriggerModule:
            module._check_trigger_condition = MagicMock(return_value=True)
    module.start()
    time.sleep(0.2)
    module.stop()
    # At least one event should have been emitted with the expected key
    assert any(event_key in e for e in events), f"No event with key '{event_key}' emitted by {ModuleClass.__name__}"

def test_manual_trigger():
    # Example: SerialTriggerModule emits trigger event when value meets condition
    manifest = {"name": "SerialTriggerModule"}
    config = {"serial_port": "COM1", "baud_rate": 9600, "logic_operator": ">", "threshold_value": 0.0}
    module = SerialTriggerModule(config, manifest)
    events = []
    module.add_event_callback(lambda data: events.append(data))
    module._check_trigger_condition = MagicMock(return_value=True)
    module._open_serial = MagicMock(return_value=True)
    module.serial_conn = MagicMock()
    module.serial_conn.in_waiting = 1
    module.serial_conn.readline = MagicMock(return_value=b"1.0\n")
    module.start()
    time.sleep(0.1)
    module.stop()
    assert any(e.get("trigger") for e in events), "Manual trigger did not emit trigger event" 