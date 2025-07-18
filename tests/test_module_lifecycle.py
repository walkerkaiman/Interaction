import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import threading
import time
import pytest
from modules.time_input_trigger.clock_input import TimeInputModule
from modules.serial_input_streaming.serial_input import SerialInputModule
from modules.serial_input_trigger.serial_trigger import SerialTriggerModule

# Helper to count threads with a given name prefix

def count_threads_with_prefix(prefix):
    return sum(1 for t in threading.enumerate() if t.name.startswith(prefix))

@pytest.mark.parametrize("ModuleClass, config", [
    (TimeInputModule, {"target_time": "12:00:00"}),
    (SerialInputModule, {"serial_port": "COM1", "baud_rate": 9600}),
    (SerialTriggerModule, {"serial_port": "COM1", "baud_rate": 9600, "logic_operator": ">", "threshold_value": 0.5}),
])
def test_start_stop_thread_cleanup(ModuleClass, config):
    manifest = {"name": ModuleClass.__name__}
    module = ModuleClass(config, manifest)
    module.start()
    time.sleep(0.1)  # Allow thread to start
    module.stop()
    time.sleep(0.1)  # Allow thread to stop
    # After stop, ensure no lingering threads with module class name
    assert not any(module.__class__.__name__ in t.name for t in threading.enumerate()), f"Thread leak for {ModuleClass.__name__}"

def test_restart_robustness():
    manifest = {"name": "TimeInputModule"}
    module = TimeInputModule({"target_time": "12:00:00"}, manifest)
    for _ in range(3):
        module.start()
        time.sleep(0.05)
        module.stop()
        time.sleep(0.05)
    # No thread leaks
    assert not any("TimeInputModule" in t.name for t in threading.enumerate()) 