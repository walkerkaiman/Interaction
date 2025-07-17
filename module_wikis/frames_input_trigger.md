# sACN Frames Input Trigger Module

## Overview
The sACN Frames Input Trigger module provides synchronization capabilities for interactive art installations by monitoring sACN (Streaming ACN) frame numbers. It triggers events when frame numbers change, enabling precise timing synchronization.

**Key Features:**
- sACN frame number monitoring
- Universe 999 frame tracking
- Frame change detection
- Real-time frame display
- Network-based synchronization
- Performance optimization

## Configuration
- **Current Frame (`current_frame`)**: Latest received frame number (display only, real-time)

- **Frame Configuration:**
  - Universe: Fixed at 999 (synchronization universe)
  - Protocol: sACN (E1.31)
  - Network: Auto-detects sACN traffic
  - Frame tracking: Continuous monitoring

## Usage
1. Connect to sACN network.
2. Monitor current frame display.
3. Connect to output modules.
4. Triggers on frame changes.
5. Synchronizes with external timing.

## Advanced Usage / Integration Examples
- Detects frame number changes
- Triggers on each new frame
- Provides frame number data
- Enables precise timing
- Connect to Audio Output for synchronized audio
- Connect to DMX Output for synchronized lighting
- Connect to OSC Output for network synchronization
- Use with multiple outputs for complex sync

## Examples
- **Video/Audio Sync**: sACN Frames Input Trigger → Audio Output (synchronized_audio.wav)
- **Multi-Device Lighting**: sACN Frames Input Trigger → Multiple DMX Outputs (front_lights.csv, back_lights.csv)
- **Performance Timing**: sACN Frames Input Trigger → OSC Output (timing_events)
- **Exhibition Coordination**: sACN Frames Input Trigger → Audio Output, DMX Output, OSC Output

## Troubleshooting
- **No Frame Reception**: Check sACN network, Universe 999 traffic, timing source.
- **Wrong Frame Numbers**: Check timing source, frame rate, network settings.
- **Network Issues**: Check sACN compatibility, network configuration, firewall.
- **Synchronization Problems**: Check frame rate matching, timing accuracy, network latency.
- **Performance Issues**: Check network bandwidth, CPU usage, try lower frame rates.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 