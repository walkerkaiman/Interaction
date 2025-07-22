# Frames Input Module

## Overview
The Frames Input module provides both trigger and streaming functionality by monitoring sACN (Streaming ACN) frame numbers on Universe 999. It supports both modes in a single TypeScript class, with a mode toggle in the UI.

**TypeScript Implementation:**
- Implemented as `FramesInputModule` in TypeScript.
- Inherits from `InputModuleBase`.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- sACN frame number monitoring and streaming
- Universe 999 frame tracking
- Mode toggle: trigger (on frame change) or streaming (continuous frame numbers)
- Real-time event emission
- Network-based synchronization
- Performance optimization
- Auto-detects sACN traffic

## Architecture & Inheritance
- **Class:** `FramesInputModule`
- **Base:** `InputModuleBase`
- **Location:** `backend/src/modules/frames_input/index.ts`
- **Frontend Integration:** Real-time state, mode toggle, and frame display via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `FramesInputModule`.
- Key functions:
  - `start()`: Starts sACN listener
  - `stop()`: Stops listener
  - `onTrigger(event)`: Handles trigger event (on frame change)
  - `onStream(value)`: Handles streaming value (continuous frame numbers)
  - `initSacnListener()`: Sets up sACN listener and message handler
- Uses Node.js library: `sacn` or similar

## Configuration
- **Universe (`universe`)**: DMX universe to monitor (default: 999)
- **Current Frame (`current_frame`)**: Latest received frame number (display only, real-time)

## Usage
1. Connect to sACN network.
2. Monitor current frame display in the UI.
3. Use mode toggle in UI to switch between trigger and streaming.
4. Connect to output modules for synchronization or streaming.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Mode toggle and frame display are available in the UI.

## Example Functions
- `start()`, `stop()`, `onTrigger(event)`, `onStream(value)`, `initSacnListener()`

## Troubleshooting
- **No Frame Reception**: Check sACN network, Universe 999 traffic, timing source.
- **Wrong Frame Numbers**: Check timing source, frame rate, network settings.
- **Network Issues**: Check sACN compatibility, network configuration, firewall.
- **Performance Issues**: Check network bandwidth, CPU usage, try lower frame rates.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 