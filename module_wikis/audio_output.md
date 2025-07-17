# Audio Output Module

## Overview
The Audio Output module provides high-quality audio playback for interactive art installations. It supports WAV file playback with individual and master volume control, real-time waveform visualization, and concurrent playback. Optimized for performance, it uses vectorized waveform processing and caching.

**Key Features:**
- WAV file playback with optimized processing
- Individual and master volume control (0-100%)
- Real-time waveform generation and caching
- Concurrent audio playback support
- Performance monitoring and optimization
- Automatic resource cleanup

## Configuration
- **Audio File (`file_path`)**: Path to the WAV file to play (text input, required)
- **Volume (`volume`)**: Individual volume level (slider, 0-100, default: 100)
- **Waveform (`waveform`)**: Visual representation of the audio file (auto-generated and cached)

## Usage
1. Select an audio file using the file picker.
2. Adjust the volume slider as needed.
3. The module will automatically generate a waveform preview.
4. Connect to a trigger input module.
5. Audio will play when triggered.

## Advanced Usage / Integration Examples
- Multiple audio outputs can play simultaneously.
- Each output has independent volume control.
- Master volume affects all audio outputs globally.
- Waveform preview helps verify audio file selection.
- Connect to OSC Input for network-triggered audio.
- Connect to Serial Trigger for sensor-activated sounds.
- Connect to Clock Input for scheduled audio events.
- Use with DMX Output for synchronized light and sound.

## Examples
- **Simple Trigger Audio**: OSC Input (/trigger) → Audio Output (ding.wav, volume: 80)
- **Sensor-Activated Audio**: Serial Trigger (threshold > 500) → Audio Output (alarm.wav, volume: 100)
- **Scheduled Audio**: Clock Input (12:00:00) → Audio Output (bell.wav, volume: 90)
- **Multi-Audio Installation**: OSC Input (/play) → Multiple Audio Outputs (bass.wav, treble.wav)

## Troubleshooting
- **Audio Not Playing**: Check file path, format (WAV), and volume settings. Verify master volume.
- **Poor Performance**: Use optimized WAV files, check waveform cache, monitor CPU usage, reduce concurrent audio files.
- **File Not Found**: Verify file exists and permissions. Use absolute paths if needed.
- **Volume Issues**: Check individual and master volume, test with different files, check system audio.
- **Waveform Not Displaying**: Wait for generation, check file format, verify matplotlib installation, clear cache if needed.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 

## Manual Trigger (Play Button) Support

This module supports a manual Play (trigger) button in the frontend. This is enabled by the following flag in its manifest:

```json
"supports_manual_trigger": true
```

### How It Works
- When this flag is present and set to true, the frontend will display a Play button for this output module in the Interaction Editor.
- The Play button is hidden whenever the module's settings are changed (dirty state) and reappears after the user clicks Save/Apply.
- The Play button sends a trigger to the backend using the appropriate API endpoint for the module.

### For Developers: Adding Manual Trigger Support
- To enable this feature for a new output module, add `"supports_manual_trigger": true` to the module's `manifest.json`.
- Add the module's API endpoint to the `playEndpoints` mapping in the frontend if it is not `play_audio`.
- The frontend will automatically handle the Play button visibility and logic for all modules with this flag.

--- 