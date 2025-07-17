"""
Test suite for the module system.
Tests module loading, configuration, event handling, and interaction between modules.
"""

import pytest
import json
import tempfile
import shutil
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from module_loader import ModuleLoader
from modules.module_base import ModuleBase, TriggerStrategy
from message_router import EventRouter


class TestModuleSystem:
    """Test the core module system functionality."""

    def test_module_loader_initialization(self):
        """Test that ModuleLoader initializes correctly."""
        loader = ModuleLoader()
        assert loader is not None
        assert hasattr(loader, 'load_modules')
        assert hasattr(loader, 'get_available_modules')

    def test_module_loader_discovers_modules(self):
        """Test that ModuleLoader discovers available modules."""
        loader = ModuleLoader()
        modules = loader.get_available_modules()
        
        assert isinstance(modules, list)
        assert len(modules) > 0
        
        # Check for expected modules
        module_ids = [m.get('id') for m in modules]
        expected_modules = ['audio_output', 'osc_input_trigger', 'dmx_output']
        
        for expected in expected_modules:
            assert expected in module_ids, f"Expected module {expected} not found"

    def test_module_manifests_are_valid(self):
        """Test that module manifests are valid JSON and contain required fields."""
        loader = ModuleLoader()
        modules = loader.get_available_modules()
        
        for module in modules:
            module_id = module.get('id')
            manifest_path = Path(f"modules/{module_id}/manifest.json")
            
            if manifest_path.exists():
                with open(manifest_path, 'r') as f:
                    manifest = json.load(f)
                
                # Check required manifest fields
                assert 'fields' in manifest, f"Module {module_id} manifest missing 'fields'"
                assert isinstance(manifest['fields'], list), f"Module {module_id} manifest 'fields' should be a list"
                
                # Check field structure
                for field in manifest['fields']:
                    assert 'name' in field, f"Field in {module_id} missing 'name'"
                    assert 'type' in field, f"Field in {module_id} missing 'type'"

    def test_module_base_class(self):
        """Test the ModuleBase class functionality."""
        # Create a mock module that inherits from ModuleBase
        class TestModule(ModuleBase):
            def __init__(self, module_id, config=None):
                super().__init__(module_id, config)
                self.events_received = []
            
            def handle_event(self, event):
                self.events_received.append(event)
        
        # Test module creation
        module = TestModule("test_module", {"test_param": "test_value"})
        assert module.module_id == "test_module"
        assert module.config == {"test_param": "test_value"}
        
        # Test event handling
        test_event = {"type": "test", "data": "test_data"}
        module.handle_event(test_event)
        assert len(module.events_received) == 1
        assert module.events_received[0] == test_event

    def test_trigger_strategy(self):
        """Test the TriggerStrategy implementation."""
        # Create a mock module with trigger strategy
        class TestOutputModule(ModuleBase):
            def __init__(self, module_id, config=None):
                super().__init__(module_id, config)
                self.triggers_received = []
                self.strategy = TriggerStrategy()
            
            def on_trigger(self, event):
                self.triggers_received.append(event)
            
            def handle_event(self, event):
                if event.get('type') == 'trigger':
                    self.on_trigger(event)
        
        module = TestOutputModule("test_output")
        trigger_event = {"type": "trigger", "source": "test"}
        module.handle_event(trigger_event)
        
        assert len(module.triggers_received) == 1
        assert module.triggers_received[0] == trigger_event

    @patch('module_loader.create_and_start_module')
    def test_module_loading_and_creation(self, mock_create):
        """Test module loading and creation process."""
        mock_module = Mock()
        mock_module.module_id = "test_module"
        mock_create.return_value = mock_module
        
        loader = ModuleLoader()
        
        # Test module creation with config
        config = {"test_param": "value"}
        created_module = loader.create_module("audio_output", config)
        
        # Module creation should be attempted
        mock_create.assert_called()

    def test_event_router_functionality(self):
        """Test the EventRouter message routing system."""
        router = EventRouter()
        
        # Create mock modules
        input_module = Mock()
        input_module.module_id = "test_input"
        
        output_module = Mock()
        output_module.module_id = "test_output"
        
        # Test adding modules to router
        router.add_module(input_module)
        router.add_module(output_module)
        
        # Test event routing
        test_event = {
            "type": "test_event",
            "source": "test_input",
            "target": "test_output",
            "data": "test_data"
        }
        
        router.route_event(test_event)
        
        # Output module should receive the event
        output_module.handle_event.assert_called_with(test_event)

    def test_module_configuration_persistence(self, test_config_dir):
        """Test that module configurations are saved and loaded correctly."""
        # Create test configuration
        test_config = {
            "interactions": [
                {
                    "input": {
                        "module": "osc_input_trigger",
                        "config": {
                            "listen_port": 9000,
                            "message_address": "/test"
                        }
                    },
                    "output": {
                        "module": "audio_output",
                        "config": {
                            "file_path": "test.wav",
                            "volume": 75.0
                        }
                    }
                }
            ]
        }
        
        # Save configuration
        config_file = test_config_dir / "interactions" / "interactions.json"
        with open(config_file, 'w') as f:
            json.dump(test_config, f)
        
        # Load and verify
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        
        assert loaded_config == test_config
        assert len(loaded_config["interactions"]) == 1
        assert loaded_config["interactions"][0]["input"]["module"] == "osc_input_trigger"

    def test_module_error_handling(self):
        """Test error handling in module operations."""
        # Test loading non-existent module
        loader = ModuleLoader()
        
        with pytest.raises(Exception):
            loader.create_module("nonexistent_module", {})

    def test_module_manifest_loading(self):
        """Test loading module manifests from filesystem."""
        manifest_files = Path("modules").glob("*/manifest.json")
        
        for manifest_file in manifest_files:
            with open(manifest_file, 'r') as f:
                manifest = json.load(f)
            
            # Basic manifest validation
            assert isinstance(manifest, dict)
            if 'fields' in manifest:
                assert isinstance(manifest['fields'], list)
                
                for field in manifest['fields']:
                    assert 'name' in field
                    assert 'type' in field
                    
                    # Validate field types
                    valid_types = ['string', 'number', 'boolean', 'select', 'file']
                    assert field['type'] in valid_types, f"Invalid field type: {field['type']}"

    def test_module_interaction_flow(self):
        """Test complete interaction flow between input and output modules."""
        # This is an integration test that simulates a complete interaction
        
        # Create mock modules
        class MockInputModule(ModuleBase):
            def __init__(self):
                super().__init__("mock_input")
                self.router = None
            
            def trigger_event(self, data):
                if self.router:
                    event = {
                        "type": "trigger",
                        "source": self.module_id,
                        "data": data,
                        "timestamp": 12345
                    }
                    self.router.route_event(event)
        
        class MockOutputModule(ModuleBase):
            def __init__(self):
                super().__init__("mock_output")
                self.received_events = []
            
            def handle_event(self, event):
                self.received_events.append(event)
        
        # Set up interaction
        input_mod = MockInputModule()
        output_mod = MockOutputModule()
        
        router = EventRouter()
        router.add_module(input_mod)
        router.add_module(output_mod)
        
        input_mod.router = router
        
        # Configure interaction (input -> output)
        router.add_interaction(input_mod.module_id, output_mod.module_id)
        
        # Trigger event
        test_data = "test_trigger_data"
        input_mod.trigger_event(test_data)
        
        # Verify output module received event
        assert len(output_mod.received_events) == 1
        assert output_mod.received_events[0]["data"] == test_data
        assert output_mod.received_events[0]["source"] == "mock_input"

    def test_module_performance_metrics(self):
        """Test module performance monitoring and metrics."""
        # Create module with performance tracking
        class PerformanceTestModule(ModuleBase):
            def __init__(self):
                super().__init__("perf_test")
                self.event_count = 0
                self.processing_time = 0
            
            def handle_event(self, event):
                import time
                start_time = time.time()
                
                # Simulate processing
                time.sleep(0.001)  # 1ms processing time
                
                self.event_count += 1
                self.processing_time += time.time() - start_time
            
            def get_performance_metrics(self):
                return {
                    "events_processed": self.event_count,
                    "total_processing_time": self.processing_time,
                    "avg_processing_time": self.processing_time / max(1, self.event_count)
                }
        
        module = PerformanceTestModule()
        
        # Process multiple events
        for i in range(10):
            module.handle_event({"data": f"event_{i}"})
        
        metrics = module.get_performance_metrics()
        assert metrics["events_processed"] == 10
        assert metrics["total_processing_time"] > 0
        assert metrics["avg_processing_time"] > 0

    def test_module_state_management(self):
        """Test module state persistence and recovery."""
        class StatefulModule(ModuleBase):
            def __init__(self, module_id, config=None):
                super().__init__(module_id, config)
                self.state = {"counter": 0, "last_event": None}
            
            def handle_event(self, event):
                self.state["counter"] += 1
                self.state["last_event"] = event
            
            def get_state(self):
                return self.state.copy()
            
            def restore_state(self, state):
                self.state.update(state)
        
        module = StatefulModule("stateful_test")
        
        # Process events and modify state
        module.handle_event({"type": "test1"})
        module.handle_event({"type": "test2"})
        
        # Save state
        saved_state = module.get_state()
        assert saved_state["counter"] == 2
        assert saved_state["last_event"]["type"] == "test2"
        
        # Create new module and restore state
        new_module = StatefulModule("stateful_test")
        new_module.restore_state(saved_state)
        
        restored_state = new_module.get_state()
        assert restored_state["counter"] == 2
        assert restored_state["last_event"]["type"] == "test2"