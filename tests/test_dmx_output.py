#!/usr/bin/env python3
"""
Test script for DMX Output Streaming Module

This script tests the DMX output module with different protocols and configurations.
"""

import sys
import os
import time
import json

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module_loader import ModuleLoader
from modules.dmx_output_streaming.dmx_output import DMXOutputModule

def test_dmx_module():
    """Test the DMX output module with different configurations."""
    
    # Load the manifest
    loader = ModuleLoader()
    manifest = loader.load_manifest("dmx_output_streaming")
    
    if not manifest:
        print("❌ Failed to load DMX output manifest")
        return False
    
    # Type assertion for manifest
    manifest = manifest  # type: ignore
    
    print("✅ DMX output manifest loaded successfully")
    print(f"Module: {manifest.get('name')}")
    print(f"Type: {manifest.get('type')}")
    print(f"Classification: {manifest.get('classification')}")
    
    # Test different configurations
    test_configs = [
        {
            "name": "sACN Configuration",
            "config": {
                "protocol": "sacn",
                "universe": 1,
                "ip_address": "127.0.0.1",
                "port": 5568,
                "csv_file": ""
            }
        },
        {
            "name": "Art-Net Configuration", 
            "config": {
                "protocol": "artnet",
                "universe": 1,
                "ip_address": "127.0.0.1",
                "port": 6454,
                "net": 0,
                "subnet": 0,
                "csv_file": ""
            }
        },
        {
            "name": "Serial Configuration",
            "config": {
                "protocol": "serial",
                "serial_port": "COM1",
                "baud_rate": 57600,
                "csv_file": ""
            }
        }
    ]
    
    for test_config in test_configs:
        print(f"\n🧪 Testing {test_config['name']}")
        
        # Create module instance
        try:
            module = DMXOutputModule(
                test_config['config'],
                manifest,
                log_callback=print
            )
            print(f"✅ {test_config['name']} - Module created successfully")
            
            # Test CSV loading
            if hasattr(module, 'dmx_frames') and module.dmx_frames:
                print(f"✅ {test_config['name']} - Loaded {len(module.dmx_frames)} DMX frames")
                
                # Test modulo index handling
                test_indices = [0, 100, 511, 512, 1000]
                for idx in test_indices:
                    frame_idx = idx % len(module.dmx_frames)
                    print(f"   Index {idx} -> Frame {frame_idx}")
            else:
                print(f"❌ {test_config['name']} - No DMX frames loaded")
            
            # Test event handling
            test_events = [
                {"index": 0},
                {"index": 100},
                {"index": 511}
            ]
            
            for event in test_events:
                print(f"   Testing event: {event}")
                module.handle_event(event)
            
            # Clean up
            module.stop()
            print(f"✅ {test_config['name']} - Module stopped successfully")
            
        except Exception as e:
            print(f"❌ {test_config['name']} - Error: {e}")
            continue
    
    print("\n🎉 DMX output module testing completed!")

def test_csv_loading():
    """Test CSV file loading functionality."""
    print("\n📄 Testing CSV file loading...")
    
    # Test with default CSV
    loader = ModuleLoader()
    manifest = loader.load_manifest("dmx_output_streaming")
    
    config = {
        "protocol": "sacn",
        "universe": 1,
        "csv_file": ""  # Empty to use default
    }
    
    try:
        module = DMXOutputModule(config, manifest, log_callback=print)
        
        if hasattr(module, 'dmx_frames') and module.dmx_frames:
            print(f"✅ Default CSV loaded: {len(module.dmx_frames)} frames")
            
            # Check first few frames
            for i in range(min(5, len(module.dmx_frames))):
                frame = module.dmx_frames[i]
                print(f"   Frame {i}: Channel {i} = {frame[i]}, others = 0")
        else:
            print("❌ Failed to load default CSV")
        
        module.stop()
        
    except Exception as e:
        print(f"❌ CSV loading test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting DMX Output Module Tests")
    print("=" * 50)
    
    test_dmx_module()
    test_csv_loading()
    
    print("\n" + "=" * 50)
    print("🏁 All tests completed!") 