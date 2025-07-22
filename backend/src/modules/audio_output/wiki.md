# Audio Output Module

## Overview
The Audio Output module provides high-quality audio playback for interactive art installations. It supports WAV file playback with individual and master volume control, real-time waveform visualization, and concurrent playback. Optimized for performance, it uses vectorized waveform processing and caching.

**TypeScript Implementation:**
- This module is implemented in TypeScript as `AudioOutputModule`.
- Inherits from `OutputModuleBase`.
- Integrated with the real-time backend/frontend architecture for live UI sync.

**Key Features:**
- WAV file playback with optimized processing
- Individual and master volume control (0-100%)
- Real-time waveform generation and caching
- Concurrent audio playback support
- Performance monitoring and optimization
- Automatic resource cleanup
- Manual trigger (play button) support

## Architecture & Inheritance
- **Class:** `AudioOutputModule`
- **Base:** `OutputModuleBase`
- **Location:** `backend/src/modules/audio_output/index.ts`
- **Frontend Integration:** Real-time state and manual trigger via WebSocket/HTTP

## Developer Guide
- Extend or modify by editing `AudioOutputModule`.
- Key functions:
  - `start()`: Preloads waveform, prepares for playback
  - `stop()`: Stops playback and cleans up
  - `onTriggerEvent(event)`: Plays audio on trigger
  - `onStreamingEvent(event)`: (Optional) For streaming mode, currently same as trigger
  - `playAudio(filePath, volume)`: Handles WAV playback
  - `generateWaveform(filePath)`: Generates and caches waveform image
  - `manualTrigger()`: Supports manual play from UI
  - `setMasterVolume(vol)`: Sets global master volume
- Use Node.js libraries: `play-sound`, `wav-decoder`, `canvas`

## Configuration
- **Audio File (`file_path`)**: Path to the WAV file to play (text input, required)
- **Volume (`volume`)**: Individual volume level (slider, 0-100, default: 100)
- **Waveform (`waveform`)**: Visual representation of the audio file (auto-generated and cached)

## Usage
1. Select an audio file using the file picker.
2. Adjust the volume slider as needed.
3. The module will automatically generate a waveform preview.
4. Connect to a trigger or streaming input module.
5. Audio will play when triggered or streamed.

## Real-Time Sync
- All settings and state changes are synced with the UI via WebSocket and HTTP.
- Manual trigger/play button is available in the UI.

## Example Functions
- `start()`, `stop()`, `onTriggerEvent(event)`, `onStreamingEvent(event)`, `playAudio(filePath, volume)`, `generateWaveform(filePath)`, `manualTrigger()`, `setMasterVolume(vol)`

## Troubleshooting
- **Audio Not Playing**: Check file path, format (WAV), and volume settings. Verify master volume.
- **Poor Performance**: Use optimized WAV files, check waveform cache, monitor CPU usage, reduce concurrent audio files.
- **File Not Found**: Verify file exists and permissions. Use absolute paths if needed.
- **Volume Issues**: Check individual and master volume, test with different files, check system audio.
- **Waveform Not Displaying**: Wait for generation, check file format, verify dependencies, clear cache if needed.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 