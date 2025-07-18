import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import tempfile
import json
from modules.time_input_trigger.clock_input import TimeInputModule

def test_save_and_load_module_config():
    manifest = {"name": "TimeInputModule"}
    config = {"target_time": "12:34:56"}
    module = TimeInputModule(config, manifest)
    # Save config to a temp file
    with tempfile.NamedTemporaryFile('w+', delete=False) as tf:
        json.dump(module.get_config(), tf)
        tf.flush()
        tf.seek(0)
        # Load config from file
        loaded_config = json.load(tf)
    assert loaded_config["target_time"] == "12:34:56"
    # Simulate restoring module from loaded config
    restored_module = TimeInputModule(loaded_config, manifest)
    assert restored_module.target_time == "12:34:56" 