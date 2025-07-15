#!/usr/bin/env python3
"""
Test script for the DMX Output Module Chase Functionality

This script tests the DMX output module's ability to play through all frames
in a CSV file when triggered, simulating both trigger and streaming input events.

Usage:
    python test_dmx_chase.py

Author: Interaction Framework Team
License: MIT
"""

import sys
import os
import time
import json

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from module_loader import ModuleLoader
from modules.dmx_output_streaming.dmx_output_streaming import DMXOutputModule

def test_dmx_chase():
    """Test the DMX output module's chase functionality."""
    
    print("🧪 Testing DMX Output Module Chase Functionality")
    print("=" * 60)
    
    # Create module loader
    loader = ModuleLoader()
    
    # Test configuration
    config = {
        "protocol": "sacn",
        "csv_file": "config/default_dmx.csv",
        "fps": "5",  # Slow FPS for testing
        "universe": "1",
        "ip_address": "127.0.0.1",
        "port": "5568"
    }
    
    # Load manifest
    manifest = loader.load_manifest("dmx_output_streaming")
    if not manifest:
        print("❌ Failed to load manifest for dmx_output_streaming")
        return False
    
    print(f"✅ Loaded manifest: {manifest['name']}")
    print(f"   Classification: {manifest.get('classification', 'unknown')}")
    print(f"   Mode: {manifest.get('mode', 'unknown')}")
    
    # Create module instance
    try:
        module = DMXOutputModule(config, manifest, log_callback=print)
        print("✅ Created DMX output module instance")
    except Exception as e:
        print(f"❌ Failed to create module instance: {e}")
        return False
    
    # Test 1: Trigger mode with chase
    print("\n🔘 Test 1: Trigger Mode with Chase")
    print("-" * 40)
    
    # Set input classification to trigger
    module.set_input_classification("trigger")
    
    # Simulate trigger event
    trigger_event = {
        "data": {
            "trigger": True,
            "value": 1.0,
            "timestamp": time.time()
        }
    }
    
    print("📤 Sending trigger event to start chase...")
    module.handle_event(trigger_event)
    
    # Wait for chase to complete (estimate based on FPS and typical frame count)
    print("⏳ Waiting for chase to complete...")
    time.sleep(3)  # Adjust based on your CSV file size and FPS
    
    # Test 2: Streaming mode
    print("\n🔘 Test 2: Streaming Mode")
    print("-" * 40)
    
    # Set input classification to streaming
    module.set_input_classification("streaming")
    
    # Simulate streaming events with different frame numbers
    streaming_events = [
        {"data": {"value": 0, "timestamp": time.time()}},
        {"data": {"value": 1, "timestamp": time.time()}},
        {"data": {"value": 2, "timestamp": time.time()}},
        {"data": {"value": 0, "timestamp": time.time()}}  # Back to first frame
    ]
    
    for i, event in enumerate(streaming_events, 1):
        print(f"📤 Sending streaming event {i}: frame {event['data']['value']}")
        module.handle_event(event)
        time.sleep(0.5)  # Brief delay between events
    
    # Test 3: Auto-detection mode
    print("\n🔘 Test 3: Auto-Detection Mode")
    print("-" * 40)
    
    # Reset to unknown mode
    module.set_input_classification("unknown")
    
    # Test auto-detection with trigger-like event
    auto_trigger_event = {
        "data": {
            "trigger": True,
            "value": 1.0,
            "timestamp": time.time()
        }
    }
    
    print("📤 Sending auto-detection trigger event...")
    module.handle_event(auto_trigger_event)
    
    # Wait briefly for chase to start
    time.sleep(1)
    
    # Test auto-detection with streaming-like event
    auto_streaming_event = {
        "data": {
            "value": 5,
            "timestamp": time.time()
        }
    }
    
    print("📤 Sending auto-detection streaming event...")
    module.handle_event(auto_streaming_event)
    
    # Display final status
    print("\n📊 Final Module Status")
    print("-" * 40)
    display_data = module.get_display_data()
    for key, value in display_data.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    module.stop()
    print("\n✅ Test completed successfully!")
    
    return True

if __name__ == "__main__":
    success = test_dmx_chase()
    sys.exit(0 if success else 1) 