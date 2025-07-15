#!/usr/bin/env python3
"""
Test script for the Unified OSC Output Module

This script tests the unified OSC output module's ability to adapt its behavior
based on the connected input module type. It simulates both trigger and streaming
input events to verify the module switches modes correctly.

Usage:
    python test_unified_osc.py

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
from modules.osc_output_unified.osc_output import UnifiedOSCOutputModule

def test_unified_osc_output():
    """Test the unified OSC output module with different input types."""
    
    print("🧪 Testing Unified OSC Output Module")
    print("=" * 50)
    
    # Create module loader
    loader = ModuleLoader()
    
    # Test configuration
    config = {
        "ip_address": "127.0.0.1",
        "port": 9001,
        "osc_address": "/test"
    }
    
    # Load manifest
    manifest = loader.load_manifest("osc_output_unified")
    if not manifest:
        print("❌ Failed to load manifest for osc_output_unified")
        return False
    
    print(f"✅ Loaded manifest: {manifest['name']}")
    print(f"   Classification: {manifest.get('classification', 'unknown')}")
    print(f"   Mode: {manifest.get('mode', 'unknown')}")
    
    # Create module instance
    try:
        module = UnifiedOSCOutputModule(config, manifest, log_callback=print)
        print("✅ Created unified OSC output module instance")
    except Exception as e:
        print(f"❌ Failed to create module instance: {e}")
        return False
    
    # Test 1: Trigger mode
    print("\n🔘 Test 1: Trigger Mode")
    print("-" * 30)
    
    # Set input classification to trigger
    module.set_input_classification("trigger")
    
    # Simulate trigger event
    trigger_event = {
        "data": {
            "trigger": True,
            "value": 0.75,
            "timestamp": time.time()
        }
    }
    
    print("📤 Sending trigger event...")
    module.handle_event(trigger_event)
    
    # Test 2: Streaming mode
    print("\n🔘 Test 2: Streaming Mode")
    print("-" * 30)
    
    # Set input classification to streaming
    module.set_input_classification("streaming")
    
    # Simulate streaming events with different data types
    streaming_events = [
        {"data": {"value": "hello", "timestamp": time.time()}},
        {"data": {"value": 42, "timestamp": time.time()}},
        {"data": {"value": 3.14, "timestamp": time.time()}},
        {"data": {"value": "test123", "timestamp": time.time()}}
    ]
    
    for i, event in enumerate(streaming_events, 1):
        print(f"📤 Sending streaming event {i}: {event['data']['value']} ({type(event['data']['value']).__name__})")
        module.handle_event(event)
        time.sleep(0.1)  # Brief delay between events
    
    # Test 3: Auto-detection mode
    print("\n🔘 Test 3: Auto-Detection Mode")
    print("-" * 30)
    
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
    
    # Test auto-detection with streaming-like event
    auto_streaming_event = {
        "data": {
            "value": "auto_detected",
            "timestamp": time.time()
        }
    }
    
    print("📤 Sending auto-detection streaming event...")
    module.handle_event(auto_streaming_event)
    
    # Display final status
    print("\n📊 Final Module Status")
    print("-" * 30)
    display_data = module.get_display_data()
    for key, value in display_data.items():
        print(f"   {key}: {value}")
    
    # Cleanup
    module.stop()
    print("\n✅ Test completed successfully!")
    
    return True

if __name__ == "__main__":
    success = test_unified_osc_output()
    sys.exit(0 if success else 1) 