# OSC Output Module

## Overview
The OSC Output module is a unified, adaptive output system that automatically detects the type of connected input module and adjusts its behavior accordingly. It supports both trigger and streaming modes in a single TypeScript class.

**TypeScript Implementation:**
- Implemented as `OscOutputModule` in TypeScript.
- Inherits from `OutputModuleBase`.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- Automatic mode detection (trigger vs streaming)
- Unified configuration interface
- Multiple OSC address support
- Network connectivity monitoring
- Performance optimization
- Error handling and recovery
- Manual trigger (play button) support

## Architecture & Inheritance
- **Class:** `OscOutputModule`
- **Base:** `OutputModuleBase`
- **Location:** `backend/src/modules/osc_output/index.ts`
- **Frontend Integration:** Real-time state and manual trigger via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `OscOutputModule`.
- Key functions:
  - `start()`: Initializes OSC UDP port
  - `stop()`: Closes UDP port
  - `onTriggerEvent(event)`: Sends OSC message on trigger
  - `onStreamingEvent(event)`: Sends OSC message on streaming data
  - `sendOscMessage(value)`: Sends OSC message to configured address/port
  - `manualTrigger()`: Supports manual play from UI
- Uses Node.js library: `osc`

## Configuration
- **IP Address (`ip_address`)**: Target IP address for OSC messages (text input, default: 127.0.0.1)
- **Port (`port`)**: UDP port for OSC communication (text input, default: 8000)
- **OSC Address (`address`)**: OSC address pattern to send (text input, default: /trigger)

## Usage
1. Configure IP address and port.
2. Set OSC address pattern.
3. Connect to any input module (trigger or streaming).
4. Module automatically adapts behavior.
5. OSC messages sent based on input type.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Manual trigger/play button is available in the UI.

## Example Functions
- `start()`, `stop()`, `onTriggerEvent(event)`, `onStreamingEvent(event)`, `sendOscMessage(value)`, `manualTrigger()`

## Troubleshooting
- **OSC Messages Not Received**: Check IP address, port, network connectivity, firewall, and receiving application.
- **Wrong Message Format**: Check OSC address pattern, data type compatibility, and receiving application format.
- **Network Connectivity**: Ping target IP, check router/firewall, test with localhost.
- **Performance Issues**: Reduce message frequency, check bandwidth, monitor CPU usage.
- **Mode Detection Issues**: Check input module classification, verify connections, restart if needed.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 