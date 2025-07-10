import time
import sacn

# Configuration
UNIVERSE = 999          # Arbitrary universe for frame sync
FPS = 30                # Frame rate
MAX_FRAME = 65535       # Max frame number before wrapping

# Start sACN sender
sender = sacn.sACNsender()
sender.start()
sender.activate_output(UNIVERSE)
sender[UNIVERSE].multicast = True

print(f"🚀 Broadcasting frame numbers on sACN universe {UNIVERSE} at {FPS} FPS")

frame = 0
try:
    while True:
        msb = (frame >> 8) & 0xFF
        lsb = frame & 0xFF

        # Construct DMX packet: first two channels = frame number
        dmx_data = [msb, lsb] + [0] * 510
        sender[UNIVERSE].dmx_data = dmx_data

        print(f"🕒 Sent frame: {frame:05d} (MSB: {msb}, LSB: {lsb})")

        frame = (frame + 1) % (MAX_FRAME + 1)
        time.sleep(1 / FPS)
except KeyboardInterrupt:
    print("\n🛑 Stopping frame sender.")
    sender.stop()
