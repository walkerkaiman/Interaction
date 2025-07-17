# sACN Frames Input Streaming Module

## Overview
The sACN Frames Input Streaming module listens for sACN frame numbers on Universe 999 and streams frame numbers as events. It is designed for real-time synchronization and streaming applications in interactive art installations.

**Key Features:**
- sACN frame number streaming
- Universe 999 frame tracking
- Real-time event streaming
- Network-based synchronization
- Performance optimization

## Configuration
- **Current Frame (`frame_number`)**: Latest received frame number (display only, real-time)

- **Frame Configuration:**
  - Universe: Fixed at 999 (synchronization universe)
  - Protocol: sACN (E1.31)
  - Network: Auto-detects sACN traffic
  - Frame tracking: Continuous monitoring

## Usage
1. Connect to sACN network.
2. Monitor current frame display.
3. Connect to streaming output modules.
4. Streams frame numbers as events.
5. Enables real-time synchronization.

## Advanced Usage / Integration Examples
- Connect to OSC Output for network streaming
- Connect to DMX Output for dynamic lighting
- Connect to Audio Output for audio control
- Use with multiple outputs for complex installations

## Examples
- **Real-Time Lighting Control**: sACN Frames Input Streaming → DMX Output (adaptive mode)
- **Audio Level Control**: sACN Frames Input Streaming → Audio Output (volume control)
- **Network Data Streaming**: sACN Frames Input Streaming → OSC Output (streaming mode)
- **Multi-Output Installation**: sACN Frames Input Streaming → DMX Output, OSC Output, Audio Output

## Troubleshooting
- **No Data Streaming**: Check sACN network, Universe 999 traffic, timing source.
- **Wrong Frame Numbers**: Check timing source, frame rate, network settings.
- **Network Issues**: Check sACN compatibility, network configuration, firewall.
- **Performance Issues**: Check network bandwidth, CPU usage, try lower frame rates.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 