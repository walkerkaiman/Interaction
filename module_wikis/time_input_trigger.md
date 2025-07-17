# Clock Input Module

## Overview
The Clock Input module provides time-based triggering for scheduled events in interactive art installations. It monitors the current system time and triggers when it matches a specified target time.

**Key Features:**
- Real-time clock monitoring
- Configurable target time (HH:MM:SS)
- Live countdown display
- Daily recurring triggers
- High-precision timing
- Performance optimization

## Configuration
- **Target Time (`target_time`)**: Time to trigger event (text input, format: HH:MM:SS, default: 12:00:00)
- **Current Time (`current_time`)**: Live display of current time (display only, real-time)
- **Time Until Target (`countdown`)**: Countdown to target time (display only, real-time)

## Usage
1. Set target time in HH:MM:SS format.
2. Monitor current time display.
3. Watch countdown to target.
4. Connect to output modules.
5. Event triggers at exact time.

## Advanced Usage / Integration Examples
- Time Format Examples:
  - "09:30:00" - 9:30 AM
  - "14:15:30" - 2:15:30 PM
  - "23:59:59" - 11:59:59 PM
  - "00:00:00" - Midnight
- Scheduling Examples:
  - Daily opening: "09:00:00"
  - Lunch break: "12:00:00"
  - Evening show: "19:30:00"
  - Closing time: "22:00:00"
- Integration Examples:
  - Connect to Audio Output for scheduled sounds
  - Connect to DMX Output for timed lighting
  - Connect to OSC Output for network events
  - Use with multiple outputs for complex schedules

## Examples
- **Daily Opening**: Target Time: 09:00:00 → Audio Output (opening_music.wav)
- **Hourly Chime**: Target Time: 00:00:00 → Audio Output (chime.wav)
- **Evening Show**: Target Time: 19:30:00 → Audio Output (show_music.wav), DMX Output (show_lights.csv)
- **Exhibition Schedule**: Multiple target times for different events

## Troubleshooting
- **Time Not Triggering**: Check time format, system clock, module connections.
- **Wrong Time Display**: Check system time, timezone configuration.
- **Countdown Issues**: Verify target time is in future, check for date rollover.
- **Performance Issues**: Check CPU usage, reduce update frequency if needed.
- **Timezone Problems**: Use local system time, check timezone settings.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 