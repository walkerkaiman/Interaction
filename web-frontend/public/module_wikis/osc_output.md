# OSC Output Module

## Overview
The OSC Output module is a unified, adaptive output system that automatically detects the type of connected input module and adjusts its behavior accordingly. This eliminates the need for separate trigger and streaming OSC modules.

**Key Features:**
- Automatic mode detection (trigger vs streaming)
- Unified configuration interface
- Multiple OSC address support
- Network connectivity monitoring
- Performance optimization
- Error handling and recovery

## Configuration
- **IP Address (`ip_address`)**: Target IP address for OSC messages (text input, default: 127.0.0.1)
- **Port (`port`)**: UDP port for OSC communication (text input, default: 8000)
- **OSC Address (`osc_address`)**: OSC address pattern to send (text input, default: /data)

## Usage
1. Configure IP address and port.
2. Set OSC address pattern.
3. Connect to any input module.
4. Module automatically adapts behavior.
5. OSC messages sent based on input type.

## Advanced Usage / Integration Examples
- Trigger Mode: Sends single OSC message on event (e.g., /trigger 0.75).
- Streaming Mode: Sends continuous OSC data (e.g., /data [0.1, 0.2, 0.3, ...]).
- Local: Use 127.0.0.1 for same computer.
- Network: Use target device IP address.
- Firewall: Ensure UDP port is open.
- Router: Configure port forwarding if needed.

## Examples
- **Local OSC Communication**: Serial Trigger → OSC Output (127.0.0.1:8000, /sensor)
- **Network OSC Control**: Clock Input (12:00:00) → OSC Output (192.168.1.100:8000, /schedule)
- **Streaming Data**: Serial Input (continuous data) → OSC Output (127.0.0.1:8000, /stream)
- **Multi-Device Control**: OSC Input (/control) → Multiple OSC Outputs (different IPs/addresses)

## Troubleshooting
- **OSC Messages Not Received**: Check IP address, port, network connectivity, firewall, and receiving application.
- **Wrong Message Format**: Check OSC address pattern, data type compatibility, and receiving application format.
- **Network Connectivity**: Ping target IP, check router/firewall, test with localhost.
- **Performance Issues**: Reduce message frequency, check bandwidth, monitor CPU usage.
- **Mode Detection Issues**: Check input module classification, verify connections, restart if needed.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 