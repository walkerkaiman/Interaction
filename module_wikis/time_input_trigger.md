# Time Input Module

This module provides a time-based trigger for your interactions. It emits events at a specified time of day, allowing you to schedule actions or synchronize with real-world clocks.

## Features
- Triggers events at a specific time of day
- Provides current time and countdown to the next trigger

## Configuration Fields
- **Target Time**: The time of day to trigger the event (HH:MM:SS)

## Usage
Add the Time Input module as an input to your interaction. Configure the target time as needed. The module will emit events with the current time and countdown, and trigger the output when the countdown reaches zero.

## Example Event
```
{
  "current_time": "14:30:00",
  "countdown": "00:15:00",
  "target_time": "14:45:00",
  "instance_id": "..."
}
```

## Notes
- The module uses the system clock of the host machine.
- Ensure the system time is accurate for reliable triggering. 