from pythonosc.udp_client import SimpleUDPClient
import time

# Set these values to match your OSC Audio Player
TARGET_IP = "127.0.0.1"  # Use your computer's IP or 127.0.0.1 if local
TARGET_PORT = 9001       # Match the OSC port in the GUI
OSC_ADDRESS = "/play"    # Match the OSC address entered in the GUI

# Create the OSC client
client = SimpleUDPClient(TARGET_IP, TARGET_PORT)

# Send test messages
# print(f"Sending OSC messages to {TARGET_IP}:{TARGET_PORT} at address {OSC_ADDRESS}")

client.send_message(OSC_ADDRESS, f"test {1}")
# print(f"Sent: {OSC_ADDRESS} test {1}")