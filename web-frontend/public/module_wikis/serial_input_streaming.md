# Serial Input Streaming Module

## Overview
The Serial Input Streaming module provides continuous data streaming from serial devices to output modules. Unlike the Serial Trigger module, it streams all incoming data without filtering or threshold conditions.

**Key Features:**
- Continuous serial data streaming
- Real-time value transmission
- Connection status monitoring
- Multiple baud rate support
- Automatic port detection
- Performance optimization

## Configuration
- **Serial Port (`port`)**: COM port to stream from (dropdown, auto-detect, required)
- **Baud Rate (`baud_rate`)**: Serial communication speed (dropdown, default: 9600)
- **Connection Status (`connection_status`)**: Current connection state (display only, real-time)
- **Current Value (`current_value`)**: Latest received value (display only, real-time)

## Usage
1. Select available serial port.
2. Choose appropriate baud rate.
3. Monitor connection status.
4. Watch current value updates.
5. Connect to streaming output modules.
6. Data streams continuously.

## Advanced Usage / Integration Examples
- Data Flow:
  - Serial device → Serial Input → Output modules
  - Continuous streaming operation
  - Real-time value transmission
  - No event filtering
- Integration Examples:
  - Connect to OSC Output for network streaming
  - Connect to DMX Output for dynamic lighting
  - Connect to Audio Output for audio control
  - Use with multiple outputs for complex installations

## Examples
- **Real-Time Lighting Control**: Serial Input (light sensor) → DMX Output (adaptive mode)
- **Audio Level Control**: Serial Input (microphone level) → Audio Output (volume control)
- **Network Data Streaming**: Serial Input (sensor data) → OSC Output (streaming mode)
- **Multi-Output Installation**: Serial Input (environmental sensors) → DMX Output, OSC Output, Audio Output

## Troubleshooting
- **No Data Streaming**: Check port selection, baud rate, device output, restart if needed.
- **Intermittent Data**: Check cable quality, power supply, try different baud rates.
- **Wrong Data Values**: Verify data format, check parsing logic, monitor raw data.
- **Performance Issues**: Reduce baud rate, check for data overflow, monitor CPU usage.
- **Connection Problems**: Check cables, device power, drivers, restart application.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 