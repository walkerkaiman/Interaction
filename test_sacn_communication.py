#!/usr/bin/env python3
"""
Simple test to verify sACN communication
"""

import sacn
import time
import threading

def dmx_callback(packet):
    print(f"✅ Received DMX data on universe {packet.universe}")
    print(f"   DMX data: {packet.dmxData[:5]}...")
    
    # Extract frame number from channels 1 and 2
    msb = packet.dmxData[0] if len(packet.dmxData) > 0 else 0
    lsb = packet.dmxData[1] if len(packet.dmxData) > 1 else 0
    frame_number = (msb << 8) | lsb
    print(f"   Frame number: {frame_number}")

def sender_test():
    """Test sender"""
    print("🔧 Starting sACN sender test...")
    
    sender = sacn.sACNsender()
    sender.start()
    sender.activate_output(1)
    
    # Set universe for output 1
    if sender[1] is not None:
        sender[1].universe = 999
        print(f"📡 Sender configured for Universe 999")
    
    # Send a few test frames
    for frame in range(1, 6):
        # Encode frame number
        msb = (frame >> 8) & 0xFF
        lsb = frame & 0xFF
        
        # Create DMX data
        dmx_data = [0] * 512
        dmx_data[0] = msb  # Channel 1
        dmx_data[1] = lsb  # Channel 2
        
        # Send data
        if sender[1] is not None:
            sender[1].dmx_data = tuple(dmx_data)
            print(f"📤 Sent frame {frame} (MSB: {msb}, LSB: {lsb})")
        else:
            print(f"❌ Failed to send frame {frame} - sender output not available")
        
        time.sleep(0.5)  # Wait 500ms between frames
    
    sender.stop()
    print("🛑 Sender stopped")

def receiver_test():
    """Test receiver"""
    print("🔧 Starting sACN receiver test...")
    
    receiver = sacn.sACNreceiver()
    receiver.start()
    receiver.on_dmx_data_change = dmx_callback
    receiver.join_multicast(999)
    
    print("📡 Receiver listening on Universe 999...")
    time.sleep(3)  # Listen for 3 seconds
    
    receiver.stop()
    print("🛑 Receiver stopped")

if __name__ == "__main__":
    print("🧪 Testing sACN Communication")
    print("=" * 40)
    
    # Start receiver in background
    receiver_thread = threading.Thread(target=receiver_test, daemon=True)
    receiver_thread.start()
    
    # Wait a moment for receiver to start
    time.sleep(1)
    
    # Start sender
    sender_test()
    
    # Wait for receiver to finish
    receiver_thread.join()
    
    print("✅ Test completed") 