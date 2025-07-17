# OSC Input Trigger Module

## Overview
The OSC Input Trigger module provides network-based trigger functionality by listening for OSC (Open Sound Control) messages. It's designed for interactive art installations that need to respond to external network events.

**Key Features:**
- OSC message reception and parsing
- Configurable IP address and port
- Multiple OSC address pattern matching
- Real-time event emission
- Network connectivity monitoring
- Performance optimization

## Configuration
- **IP Address (`ip_address`)**: Network interface to listen on (display only, auto-detected, default: 0.0.0.0)
- **Port (`port`)**: UDP port to listen for OSC messages (text input, default: 8000)
- **OSC Address (`address`)**: OSC address pattern to match (text input, default: /trigger)
- **Reset (`reset`)**: Button to reset connection and clear status

## Usage
1. Configure port number (default: 8000).
2. Set OSC address pattern to listen for.
3. Connect to output modules.
4. Send OSC messages to trigger events.
5. Monitor connection status.

## Advanced Usage / Integration Examples
- OSC Message Format:
  - Address: /trigger
  - Arguments: Any OSC data type
  - Examples:
    - /trigger 0.75 (float value)
    - /play "sound1" (string)
    - /stop (no arguments)
- Testing OSC:
  - Use included test scripts
  - Send from mobile OSC apps
  - Use network debugging tools
  - Test with localhost first
- Network Setup:
  - Ensure devices are on same network
  - Check IP address configuration
  - Verify port availability
  - Test connectivity with ping

## Examples
- **Simple Trigger**: OSC Message: /trigger 1.0 → Triggers connected outputs with value 1.0
- **Named Trigger**: OSC Message: /play "effect1" → Triggers with string "effect1"
- **Multiple Addresses**: /start 1, /stop 0, /pause 0.5 → Different triggers for different actions
- **Network Installation**: Mobile app → OSC Input (192.168.1.50:8000) → /interact 0.8

## Troubleshooting
- **OSC Messages Not Received**: Check port, network, firewall, and address pattern.
- **Wrong Address Pattern**: Verify OSC address matches exactly, check for typos.
- **Network Connectivity**: Ping between devices, check IP configuration, verify subnet mask.
- **Port Already in Use**: Check for other applications, use different port, restart application.
- **Firewall Issues**: Allow UDP traffic, check firewall/router settings.

## Installation Notes
*Add your installation-specific notes here. This section is editable in the web interface.* 