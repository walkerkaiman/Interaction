# Time Input Module

## Overview
The Time Input module provides a time-based trigger for your interactions. It emits events at a specified time of day, allowing you to schedule actions or synchronize with real-world clocks. Implemented in TypeScript as a single class.

**TypeScript Implementation:**
- Implemented as `TimeInputModule` in TypeScript.
- Inherits from `InputModuleBase`.
- Appears as 'Time' in the UI dropdown.
- Integrated with real-time backend/frontend architecture for live UI sync.

**Key Features:**
- Triggers events at a specific time of day
- Provides current time and countdown to the next trigger
- Uses system clock of the host machine
- Real-time event emission and UI sync

## Architecture & Inheritance
- **Class:** `TimeInputModule`
- **Base:** `InputModuleBase`
- **Location:** `backend/src/modules/time_input_trigger/index.ts`
- **Frontend Integration:** Real-time state and countdown via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `TimeInputModule`.
- Key functions:
  - `start()`: Starts the timer
  - `stop()`: Stops the timer
  - `checkTime()`: Checks current time and triggers event
  - `onTrigger(event)`: Handles trigger event
  - `getTriggerParameters()`: Returns config for UI
- Uses standard JS Date/time functions

## Configuration
- **Target Time (`target_time`)**: The time of day to trigger the event (HH:MM:SS)

## Usage
1. Add the Time Input module as an input to your interaction.
2. Configure the target time as needed.
3. The module will emit events with the current time and countdown, and trigger the output when the countdown reaches zero.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Countdown and trigger status are updated in real time.

## Example Functions
- `start()`, `stop()`, `checkTime()`, `onTrigger(event)`, `getTriggerParameters()`

## Troubleshooting
- **No Trigger**: Check system clock, target time, and configuration.
- **Wrong Countdown**: Verify time format (HH:MM:SS), check system time zone.
- **Multiple Triggers**: Ensure only one instance is running, check last triggered date logic.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 