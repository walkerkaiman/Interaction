# Serial Input Module

## Overview
The Serial Input module provides both trigger and streaming functionality by monitoring serial data from hardware sensors. It supports both modes in a single TypeScript class, with a mode toggle in the UI.

**TypeScript Implementation:**
- Implemented as `SerialInputModule` in TypeScript.
- Inherits from `InputModuleBase`.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- Serial port monitoring and data parsing
- Mode toggle: trigger (threshold/logic) or streaming (continuous)
- Configurable logic operators (<, >, =)
- Threshold-based triggering (trigger mode)
- Continuous data streaming (streaming mode)
- Real-time value display and status
- Connection status monitoring
- Multiple baud rate support
- Auto-detect available ports
- Reset and config update support

## Architecture & Inheritance
- **Class:** `SerialInputModule`
- **Base:** `InputModuleBase`
- **Location:** `backend/src/modules/serial_input_trigger/index.ts`
- **Frontend Integration:** Real-time state, mode toggle, and reset via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `SerialInputModule`.
- Key functions:
  - `start()`: Opens serial port and starts monitoring
  - `stop()`: Closes serial port
  - `onTrigger(event)`: Handles trigger event (mode: trigger)
  - `onStream(value)`: Handles streaming value (mode: streaming)
  - `initSerial()`: Sets up serial port and data handler
  - `checkTrigger(value)`: Applies logic operator and threshold
  - `reset()`: Restarts the serial connection
- Uses Node.js library: `serialport`

## Configuration
- **Serial Port (`port`)**: COM port to monitor (auto-detect, required)
- **Baud Rate (`baud_rate`)**: Serial communication speed (default: 9600)
- **Logic Operator (`logic_operator`)**: Comparison operator (default: >)
- **Threshold Value (`threshold_value`)**: Value to compare against (default: 0)

## Usage
1. Select available serial port.
2. Choose appropriate baud rate.
3. Set logic operator and threshold (for trigger mode).
4. Use mode toggle in UI to switch between trigger and streaming.
5. Monitor connection status and current value.
6. Connect to output modules.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Mode toggle and reset are available in the UI.

## Example Functions
- `start()`, `stop()`, `onTrigger(event)`, `onStream(value)`, `initSerial()`, `checkTrigger(value)`, `reset()`

## Troubleshooting
- **No Serial Connection**: Check port selection, baud rate, device drivers.
- **Wrong Data Received**: Verify baud rate, check data format, monitor raw serial data.
- **No Triggers**: Check logic operator, threshold value, monitor current value.
- **Connection Drops**: Check cables, power supply, restart device.
- **Performance Issues**: Reduce baud rate, check for data overflow, monitor CPU usage.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 