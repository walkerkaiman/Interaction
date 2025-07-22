# DMX Output Module

## Overview
The DMX Output module provides comprehensive DMX lighting control with support for multiple protocols and adaptive behavior. It automatically switches between trigger and streaming modes based on the connected input module, all in a single TypeScript class.

**TypeScript Implementation:**
- Implemented as `DmxOutputModule` in TypeScript.
- Inherits from `OutputModuleBase`.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- Multiple protocol support (sACN, Art-Net, Serial DMX)
- Adaptive trigger/streaming modes (mode toggle)
- Chase functionality for trigger inputs
- Frame sequencing and timing control
- Network and serial connectivity
- Performance optimization
- Manual trigger (play button) support

## Architecture & Inheritance
- **Class:** `DmxOutputModule`
- **Base:** `OutputModuleBase`
- **Location:** `backend/src/modules/dmx_output/index.ts`
- **Frontend Integration:** Real-time state and manual trigger via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `DmxOutputModule`.
- Key functions:
  - `start()`: Initializes protocol and loads frames
  - `stop()`: Cleans up connections and intervals
  - `onTriggerEvent(event)`: Plays chase sequence from CSV
  - `onStreamingEvent(event)`: Sends real-time DMX data
  - `playChase()`: Runs chase mode
  - `sendDmxFrame(frame)`: Sends DMX frame via selected protocol
  - `manualTrigger()`: Supports manual play from UI
- Uses Node.js libraries: `sacn`, `artnet`, `serialport`, `csv-parse`

## Configuration
- **Protocol (`protocol`)**: DMX communication protocol (select: sACN, Art-Net, Serial DMX)
- **DMX CSV File (`csv_file`)**: Path to frame data file (file picker, required)
- **Chase FPS (`fps`)**: Frames per second for chase mode (default: 10)
- **Universe (`universe`)**: DMX universe number (default: 1)
- **IP Address (`ip_address`)**: Target IP for network protocols (default: 127.0.0.1)
- **Port (`port`)**: Network port for DMX (default: 5568)
- **Serial Port (`serial_port`)**: COM port for serial DMX (required for Serial DMX)
- **Net (`net`)**: Art-Net net number (default: 0)
- **Subnet (`subnet`)**: Art-Net subnet number (default: 0)

## Usage
1. Select DMX protocol (sACN recommended).
2. Choose DMX CSV file with frame data.
3. Configure network settings (IP, port, universe).
4. Set chase FPS for trigger mode.
5. Connect to input module (trigger or streaming).
6. Module adapts behavior automatically.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Manual trigger/play button is available in the UI.

## Example Functions
- `start()`, `stop()`, `onTriggerEvent(event)`, `onStreamingEvent(event)`, `playChase()`, `sendDmxFrame(frame)`, `manualTrigger()`

## Troubleshooting
- **No DMX Output**: Check protocol, IP, port, DMX device settings, and universe number.
- **CSV File Issues**: Check file format/path, verify structure, test with simple file, check permissions, validate DMX values (0-255).
- **Network Problems**: Ping target IP, check firewall, verify port, test with localhost, check router.
- **Timing Issues**: Adjust FPS, check system performance, verify frame count, test with slower FPS.
- **Protocol-Specific Issues**: sACN (universe range), Art-Net (net/subnet), Serial (COM port).

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 