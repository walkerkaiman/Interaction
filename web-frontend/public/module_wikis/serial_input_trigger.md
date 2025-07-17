# Serial Trigger Module

## Overview
The Serial Trigger module provides hardware sensor integration by monitoring serial data and triggering events when values meet specified conditions. It's designed for interactive installations that use physical sensors and hardware inputs.

**Key Features:**
- Serial port monitoring and data parsing
- Configurable logic operators (<, >, =)
- Threshold-based triggering
- Real-time value display
- Connection status monitoring
- Multiple baud rate support

## Configuration
- **Serial Port (`port`)**: COM port to monitor (dropdown, auto-detect, required)
- **Baud Rate (`baud_rate`)**: Serial communication speed (dropdown, default: 9600)
- **Logic Operator (`logic_operator`)**: Comparison operator (dropdown, default: >)
- **Threshold Value (`threshold_value`)**: Value to compare against (text input, default: 0)
- **Connection Status (`connection_status`)**: Current connection state (display only, real-time)
- **Current Value (`current_value`)**: Latest received value (display only, real-time)
- **Trigger Status (`trigger_status`)**: Current trigger state (display only, real-time)

## Usage
1. Select available serial port.
2. Choose appropriate baud rate.
3. Set logic operator and threshold.
4. Monitor connection status.
5. Watch current value updates.
6. Connect to output modules.
7. Triggers when conditions are met.

## Advanced Usage / Integration Examples
- Logic Operations:
  - > (Greater than): Triggers when value > threshold
  - < (Less than): Triggers when value < threshold
  - = (Equal): Triggers when value = threshold
- Threshold Examples:
  - Motion sensor: > 100 (triggers on movement)
  - Light sensor: < 50 (triggers in darkness)
  - Pressure sensor: > 500 (triggers on pressure)
  - Temperature: > 25 (triggers when hot)
- Serial Data Format:
  - Expects numeric values
  - One value per line recommended
  - Handles integers and decimals
  - Auto-parses incoming data

## Examples
- **Motion Detection**: PIR motion sensor > 100 → Audio Output (motion_sound.wav)
- **Light-Activated Installation**: Photoresistor < 50 → DMX Output (dark_lights.csv)
- **Pressure-Sensitive Floor**: Pressure sensor > 500 → Audio Output (step_sound.wav)
- **Temperature-Controlled Art**: Temperature sensor > 25 → DMX Output (hot_lights.csv)

## Troubleshooting
- **No Serial Connection**: Check port selection, baud rate, device drivers.
- **Wrong Data Received**: Verify baud rate, check data format, monitor raw serial data.
- **No Triggers**: Check logic operator, threshold value, monitor current value.
- **Connection Drops**: Check cables, power supply, restart device.
- **Performance Issues**: Reduce baud rate, check for data overflow, monitor CPU usage.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 