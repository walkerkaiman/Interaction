# DMX Output Module

## Overview
The DMX Output module provides comprehensive DMX lighting control with support for multiple protocols and adaptive behavior. It automatically switches between trigger and streaming modes based on the connected input module.

**Key Features:**
- Multiple protocol support (sACN, Art-Net, Serial DMX)
- Adaptive trigger/streaming modes
- Chase functionality for trigger inputs
- Frame sequencing and timing control
- Network and serial connectivity
- Performance optimization

## Configuration
- **Protocol (`protocol`)**: DMX communication protocol (select: sACN, Art-Net, Serial DMX)
- **DMX CSV File (`csv_file`)**: Path to frame data file (file picker, required)
- **Chase FPS (`fps`)**: Frames per second for chase mode (text input, default: 10)
- **Universe (`universe`)**: DMX universe number (text input, default: 1)
- **IP Address (`ip_address`)**: Target IP for network protocols (text input, default: 127.0.0.1)
- **Port (`port`)**: Network port for DMX (text input, default: 5568)
- **Serial Port (`serial_port`)**: COM port for serial DMX (select, required for Serial DMX)
- **Net (`net`)**: Art-Net net number (text input, default: 0)
- **Subnet (`subnet`)**: Art-Net subnet number (text input, default: 0)

## Usage
1. Select DMX protocol (sACN recommended).
2. Choose DMX CSV file with frame data.
3. Configure network settings (IP, port, universe).
4. Set chase FPS for trigger mode.
5. Connect to input module.
6. Module adapts behavior automatically.

## Advanced Usage / Integration Examples
- Trigger Mode: Plays through all frames in CSV file once at configured FPS.
- Streaming Mode: Maps input values to DMX channels and sends real-time DMX data.
- CSV File Format:
  - Each row represents one DMX frame.
  - Columns represent DMX channels (1-512).
  - Values range from 0-255.
  - Header row optional.

## Examples
- **Simple Light Show**: Clock Input (12:00:00) → DMX Output (sACN, light_show.csv, FPS: 10)
- **Sensor-Controlled Lighting**: Serial Input (continuous data) → DMX Output (sACN, universe: 1)
- **Multi-Universe Setup**: OSC Input (/trigger) → Multiple DMX Outputs (different universes)
- **Art-Net Installation**: Serial Trigger (threshold > 500) → DMX Output (Art-Net, net: 0, subnet: 0)

## Troubleshooting
- **No DMX Output**: Check protocol, IP, port, DMX device settings, and universe number.
- **CSV File Issues**: Check file format/path, verify structure, test with simple file, check permissions, validate DMX values (0-255).
- **Network Problems**: Ping target IP, check firewall, verify port, test with localhost, check router.
- **Timing Issues**: Adjust FPS, check system performance, verify frame count, test with slower FPS.
- **Protocol-Specific Issues**: sACN (universe range), Art-Net (net/subnet), Serial (COM port).

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 