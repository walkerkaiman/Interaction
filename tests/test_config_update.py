import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import time
from modules.time_input_trigger.clock_input import TimeInputModule
from modules.serial_input_streaming.serial_input import SerialInputModule
from modules.serial_input_trigger.serial_trigger import SerialTriggerModule

def test_config_update_applies():
    manifest = {"name": "SerialInputModule"}
    config = {"serial_port": "COM1", "baud_rate": 9600}
    module = SerialInputModule(config, manifest)
    module.start()
    time.sleep(0.05)
    new_config = {"serial_port": "COM2", "baud_rate": 115200}
    module.update_config(new_config)
    assert module.serial_port == "COM2"
    assert module.baud_rate == 115200
    module.stop()

def test_timeinput_config_update():
    manifest = {"name": "TimeInputModule"}
    config = {"target_time": "12:00:00"}
    module = TimeInputModule(config, manifest)
    module.start()
    time.sleep(0.05)
    module.update_config({"target_time": "13:00:00"})
    assert module.target_time == "13:00:00"
    module.stop() 