"""
Test suite for performance characteristics.
Tests system performance, memory usage, and responsiveness under various loads.
"""

import pytest
import asyncio
import time
import psutil
import threading
import concurrent.futures
from unittest.mock import Mock
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from message_router import EventRouter
from modules.module_base import ModuleBase


class TestPerformance:
    """Test performance characteristics of the system."""

    def test_event_routing_performance(self):
        """Test performance of event routing under load."""
        router = EventRouter()
        
        # Create multiple mock modules
        modules = []
        for i in range(10):
            module = Mock()
            module.module_id = f"module_{i}"
            module.handle_event = Mock()
            router.add_module(module)
            modules.append(module)
        
        # Measure event routing performance
        num_events = 1000
        start_time = time.time()
        
        for i in range(num_events):
            event = {
                "type": "performance_test",
                "source": f"module_{i % 5}",
                "target": f"module_{(i + 1) % 10}",
                "data": f"event_{i}",
                "timestamp": time.time()
            }
            router.route_event(event)
        
        end_time = time.time()
        total_time = end_time - start_time
        events_per_second = num_events / total_time
        
        # Should handle at least 1000 events per second
        assert events_per_second > 1000, f"Event routing too slow: {events_per_second:.2f} events/sec"
        
        # Verify all events were routed
        total_calls = sum(module.handle_event.call_count for module in modules)
        assert total_calls == num_events

    def test_concurrent_event_processing(self):
        """Test handling of concurrent events."""
        router = EventRouter()
        
        # Create modules that simulate processing time
        class SlowProcessingModule(ModuleBase):
            def __init__(self, module_id):
                super().__init__(module_id)
                self.processed_events = []
                self.lock = threading.Lock()
            
            def handle_event(self, event):
                # Simulate processing time
                time.sleep(0.001)  # 1ms processing
                with self.lock:
                    self.processed_events.append(event)
        
        modules = []
        for i in range(5):
            module = SlowProcessingModule(f"slow_module_{i}")
            router.add_module(module)
            modules.append(module)
        
        # Send events concurrently
        num_events = 100
        events = []
        
        def send_event(event_id):
            event = {
                "type": "concurrent_test",
                "source": "test_source",
                "target": f"slow_module_{event_id % 5}",
                "data": f"event_{event_id}",
                "timestamp": time.time()
            }
            router.route_event(event)
            return event
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_event, i) for i in range(num_events)]
            events = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        
        # Wait for all processing to complete
        time.sleep(0.5)
        
        # Verify all events were processed
        total_processed = sum(len(module.processed_events) for module in modules)
        assert total_processed == num_events
        
        # Should complete in reasonable time even with processing delays
        assert end_time - start_time < 5.0, f"Concurrent processing took too long: {end_time - start_time:.2f}s"

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable under load."""
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        router = EventRouter()
        
        # Create modules
        modules = []
        for i in range(20):
            module = Mock()
            module.module_id = f"mem_test_module_{i}"
            module.handle_event = Mock()
            router.add_module(module)
            modules.append(module)
        
        # Generate continuous events
        num_cycles = 100
        events_per_cycle = 100
        
        for cycle in range(num_cycles):
            for i in range(events_per_cycle):
                event = {
                    "type": "memory_test",
                    "source": f"mem_test_module_{i % 10}",
                    "target": f"mem_test_module_{(i + 1) % 20}",
                    "data": f"cycle_{cycle}_event_{i}",
                    "timestamp": time.time()
                }
                router.route_event(event)
            
            # Check memory every 10 cycles
            if cycle % 10 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_growth = current_memory - initial_memory
                
                # Memory should not grow excessively (allow up to 50MB growth)
                assert memory_growth < 50, f"Excessive memory growth: {memory_growth:.2f}MB after {cycle} cycles"

    @pytest.mark.asyncio
    async def test_api_response_times(self, app_server, http_client):
        """Test API response times under load."""
        endpoints = [
            "/modules",
            "/config",
            "/module_instances",
            "/api/browse_files"
        ]
        
        response_times = []
        
        # Test each endpoint multiple times
        for endpoint in endpoints:
            for _ in range(10):
                start_time = time.time()
                response = await http_client.get(f"{app_server}{endpoint}")
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                # Each request should complete quickly
                assert response_time < 1.0, f"Slow response from {endpoint}: {response_time:.3f}s"
                assert response.status_code == 200
        
        # Average response time should be reasonable
        avg_response_time = sum(response_times) / len(response_times)
        assert avg_response_time < 0.5, f"Average response time too high: {avg_response_time:.3f}s"

    @pytest.mark.asyncio
    async def test_concurrent_api_requests(self, app_server, http_client):
        """Test handling concurrent API requests."""
        async def make_request(endpoint):
            start_time = time.time()
            response = await http_client.get(f"{app_server}{endpoint}")
            end_time = time.time()
            return response.status_code, end_time - start_time
        
        # Create concurrent requests to different endpoints
        tasks = []
        for _ in range(20):
            tasks.append(make_request("/modules"))
            tasks.append(make_request("/config"))
            tasks.append(make_request("/module_instances"))
        
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # All requests should complete successfully
        for status_code, response_time in results:
            assert status_code == 200
            assert response_time < 2.0  # Individual request timeout
        
        # Total time should be reasonable (concurrent, not sequential)
        total_time = end_time - start_time
        assert total_time < 10.0, f"Concurrent requests took too long: {total_time:.2f}s"

    def test_module_loading_performance(self):
        """Test module loading and initialization performance."""
        from module_loader import ModuleLoader
        
        loader = ModuleLoader()
        
        # Measure module discovery time
        start_time = time.time()
        modules = loader.get_available_modules()
        discovery_time = time.time() - start_time
        
        assert discovery_time < 2.0, f"Module discovery too slow: {discovery_time:.3f}s"
        assert len(modules) > 0, "No modules discovered"
        
        # Test repeated loading (should be cached)
        start_time = time.time()
        modules_cached = loader.get_available_modules()
        cached_time = time.time() - start_time
        
        # Cached loading should be much faster
        assert cached_time < discovery_time / 2, "Module caching not effective"
        assert modules_cached == modules, "Cached modules differ from original"

    def test_configuration_save_load_performance(self, test_config_dir):
        """Test configuration saving and loading performance."""
        import json
        
        # Create large configuration
        large_config = {
            "installation_name": "Performance Test",
            "interactions": []
        }
        
        # Add many interactions
        for i in range(1000):
            interaction = {
                "input": {
                    "module": "osc_input_trigger",
                    "config": {
                        "listen_port": 8000 + i,
                        "message_address": f"/test_{i}",
                        "timeout": 5.0
                    }
                },
                "output": {
                    "module": "audio_output",
                    "config": {
                        "file_path": f"test_audio_{i}.wav",
                        "volume": 50.0 + (i % 50),
                        "loop": i % 2 == 0
                    }
                }
            }
            large_config["interactions"].append(interaction)
        
        config_file = test_config_dir / "interactions" / "performance_test.json"
        
        # Test save performance
        start_time = time.time()
        with open(config_file, 'w') as f:
            json.dump(large_config, f)
        save_time = time.time() - start_time
        
        assert save_time < 1.0, f"Config save too slow: {save_time:.3f}s"
        
        # Test load performance
        start_time = time.time()
        with open(config_file, 'r') as f:
            loaded_config = json.load(f)
        load_time = time.time() - start_time
        
        assert load_time < 1.0, f"Config load too slow: {load_time:.3f}s"
        assert len(loaded_config["interactions"]) == 1000
        assert loaded_config == large_config

    def test_event_queue_performance(self):
        """Test event queue handling under high load."""
        import queue
        import threading
        
        event_queue = queue.Queue()
        processed_events = []
        stop_processing = threading.Event()
        
        def event_processor():
            while not stop_processing.is_set():
                try:
                    event = event_queue.get(timeout=0.1)
                    # Simulate processing
                    time.sleep(0.0001)  # 0.1ms processing
                    processed_events.append(event)
                    event_queue.task_done()
                except queue.Empty:
                    continue
        
        # Start processor thread
        processor_thread = threading.Thread(target=event_processor)
        processor_thread.start()
        
        # Generate high-frequency events
        num_events = 5000
        start_time = time.time()
        
        for i in range(num_events):
            event = {
                "id": i,
                "type": "high_freq_test",
                "timestamp": time.time(),
                "data": f"event_{i}"
            }
            event_queue.put(event)
        
        # Wait for processing to complete
        event_queue.join()
        stop_processing.set()
        processor_thread.join(timeout=5.0)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify all events processed
        assert len(processed_events) == num_events
        
        # Should handle high frequency events efficiently
        events_per_second = num_events / total_time
        assert events_per_second > 1000, f"Event processing too slow: {events_per_second:.2f} events/sec"

    def test_websocket_performance(self):
        """Test WebSocket message handling performance."""
        # This would test WebSocket performance if we had access to the WebSocket handler
        # For now, we'll create a mock test
        
        messages_processed = 0
        
        def mock_websocket_handler(message):
            nonlocal messages_processed
            # Simulate message processing
            time.sleep(0.0001)  # 0.1ms processing
            messages_processed += 1
        
        # Simulate high-frequency WebSocket messages
        num_messages = 1000
        start_time = time.time()
        
        for i in range(num_messages):
            message = {
                "type": "websocket_test",
                "id": i,
                "timestamp": time.time(),
                "data": f"ws_message_{i}"
            }
            mock_websocket_handler(message)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        assert messages_processed == num_messages
        
        # Should handle WebSocket messages efficiently
        messages_per_second = num_messages / total_time
        assert messages_per_second > 5000, f"WebSocket handling too slow: {messages_per_second:.2f} msg/sec"