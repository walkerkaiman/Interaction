#!/usr/bin/env python3
"""
Test script for Serial Port Detection

This script tests the serial port detection functionality used by the DMX output module.
"""

import sys
import os

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_serial_port_detection():
    """Test the serial port detection function."""
    print("🔧 Testing Serial Port Detection")
    print("=" * 40)
    
    try:
        # Import the function from the DMX module
        from modules.dmx_output_streaming.dmx_output_streaming import get_available_serial_ports
        
        # Get available ports
        ports = get_available_serial_ports()
        
        print(f"✅ Found {len(ports)} serial ports:")
        for i, port in enumerate(ports, 1):
            print(f"   {i}. {port}")
        
        if not ports:
            print("⚠️ No serial ports found - this is normal on some systems")
        else:
            print(f"✅ Serial port detection working - first port: {ports[0]}")
            
    except Exception as e:
        print(f"❌ Error testing serial port detection: {e}")
        return False
    
    return True

def test_dmx_module_loading():
    """Test that the DMX module loads correctly."""
    print("\n🔧 Testing DMX Module Loading")
    print("=" * 40)
    
    try:
        from modules.dmx_output_streaming.dmx_output_streaming import DMXOutputModule
        from modules.module_base import ModuleBase
        
        # Check if it inherits from ModuleBase
        if issubclass(DMXOutputModule, ModuleBase):
            print("✅ DMXOutputModule correctly inherits from ModuleBase")
        else:
            print("❌ DMXOutputModule does not inherit from ModuleBase")
            return False
        
        # Test creating an instance
        config = {
            "protocol": "sacn",
            "universe": 1,
            "csv_file": ""
        }
        
        manifest = {
            "name": "DMX Output",
            "type": "output",
            "classification": "streaming"
        }
        
        module = DMXOutputModule(config, manifest, log_callback=print)
        print("✅ DMXOutputModule instance created successfully")
        
        # Test field options
        options = module.get_field_options("serial_port")
        print(f"✅ Serial port options: {options}")
        
        # Clean up
        module.stop()
        print("✅ DMXOutputModule stopped successfully")
        
    except Exception as e:
        print(f"❌ Error testing DMX module: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting Serial Port and DMX Module Tests")
    print("=" * 50)
    
    success1 = test_serial_port_detection()
    success2 = test_dmx_module_loading()
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    print("🏁 Testing completed!") 