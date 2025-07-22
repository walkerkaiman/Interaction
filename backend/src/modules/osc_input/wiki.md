# OSC Input Module

## Overview
The OSC Input module provides network-based trigger and streaming functionality by listening for OSC (Open Sound Control) messages. It supports both trigger and streaming modes in a single TypeScript class, with a mode toggle in the UI.

**TypeScript Implementation:**
- Implemented as `OscInputModule` in TypeScript.
- Inherits from `InputModuleBase`.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- OSC message reception and parsing
- Configurable UDP port and OSC address pattern
- Mode toggle: trigger (event) or streaming (continuous)
- Real-time event emission
- Network connectivity monitoring
- Performance optimization
- Reset and config update support

## Architecture & Inheritance
- **Class:** `OscInputModule`
- **Base:** `InputModuleBase`
- **Location:** `backend/src/modules/osc_input_trigger/index.ts`
- **Frontend Integration:** Real-time state, mode toggle, and reset via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `OscInputModule`.
- Key functions:
  - `start()`: Starts OSC UDP listener
  - `stop()`: Stops listener
  - `onTrigger(event)`: Handles trigger event (mode: trigger)
  - `onStream(value)`: Handles streaming value (mode: streaming)
  - `initOscListener()`: Sets up UDP port and message handler
  - `reset()`: Restarts the listener
- Uses Node.js library: `osc`

## Configuration
- **Port (`port`)**: UDP port to listen for OSC messages (default: 8000)
- **OSC Address (`address`)**: OSC address pattern to match (default: /trigger)

## Usage
1. Configure port number (default: 8000).
2. Set OSC address pattern to listen for.
3. Connect to output modules.
4. Use mode toggle in UI to switch between trigger and streaming.
5. Send OSC messages to trigger or stream events.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Mode toggle and reset are available in the UI.

## Example Functions
- `start()`, `stop()`, `onTrigger(event)`, `onStream(value)`, `initOscListener()`, `reset()`

## Troubleshooting
- **OSC Messages Not Received**: Check port, network, firewall, and address pattern.
- **Wrong Address Pattern**: Verify OSC address matches exactly, check for typos.
- **Network Connectivity**: Ping between devices, check IP configuration, verify subnet mask.
- **Port Already in Use**: Check for other applications, use different port, restart application.
- **Firewall Issues**: Allow UDP traffic, check firewall/router settings.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 