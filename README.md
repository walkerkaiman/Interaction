# Interaction - Interactive Art Installation Framework

A modular Python framework for creating interactive art installations using microservices that communicate over OSC (Open Sound Control). This system allows you to build complex interactive experiences by connecting input modules (sensors, triggers, etc.) to output modules (audio, video, lighting, etc.) through both a web-based interface and traditional GUI.

## 🏗️ Architecture Overview

### Microservice Design
The Interaction framework uses a microservice architecture where each component is a self-contained module:

- **Input Modules**: Handle external triggers (OSC messages, sensors, buttons, time-based triggers, etc.)
- **Output Modules**: Generate responses (audio playback, video, lighting, etc.)
- **Message Router**: Routes events between input and output modules with optimized performance
- **Module Loader**: Dynamically discovers and loads modules with integrated caching
- **Web Interface**: Modern React-based interface for configuration and monitoring
- **Backend API**: FastAPI-based backend with WebSocket support for real-time updates

### Core Components

```
Interaction/
├── main.py                 # Application entry point with performance management
├── gui.py                  # Legacy GUI interface (optional)
├── message_router.py       # Optimized event routing system
├── module_loader.py        # Module discovery with thread pool and config cache
├── modules/                # Module definitions
│   ├── module_base.py      # Base class for all modules with strategy patterns
│   ├── audio_output/       # Audio playback with optimized processing
│   ├── osc_output/         # Unified OSC output (trigger/streaming adaptive)
│   ├── dmx_output/         # Unified DMX output (trigger/streaming adaptive)
│   ├── osc_input_trigger/  # OSC message receiver
│   ├── time_input_trigger/ # Time-based triggers (clock, countdown)
│   ├── serial_input_trigger/ # Serial port triggers
│   ├── serial_input_streaming/ # Serial port streaming data
│   ├── frames_input_trigger/ # sACN frame triggers
│   └── frames_input_streaming/ # sACN frame streaming
├── config/                 # Configuration files
│   ├── config.json         # App-level settings
│   └── interactions/       # Installation configurations
├── web-frontend/           # React-based web interface
│   ├── src/
│   │   ├── pages/          # Main application pages
│   │   ├── components/     # Reusable UI components
│   │   ├── api/            # API client and WebSocket handling
│   │   └── state/          # State management
│   └── public/             # Static assets and module wikis
└── tests/                  # Test assets and scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 38- Node.js 16 (for web frontend development)
- Required packages (see `requirements.txt`):
  - `aiohttp` (web backend)
  - `aiohttp-cors` (CORS support)
  - `python-osc` (OSC communication)
  - `pygame` (audio playback)
  - `pydub` (audio processing)
  - `matplotlib` (waveform generation)
  - `Pillow` (image processing)
  - `pyserial` (serial communication)
  - `sacn` (sACN protocol)
  - `psutil` (system monitoring)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Interaction
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3**Install frontend dependencies** (for development)
   ```bash
   cd web-frontend
   npm install
   cd ..
   ```

4. **Run the application**
   ```bash
   # Web interface (recommended)
   python main.py
   
   # Legacy GUI interface
   python main.py --gui
   ```

The web interface will automatically open in your browser at `http://localhost:800## 📋 How to Build an Installation

### 1. Understanding the Module System

#### Module Classifications
Modules are classified by type and behavior:
- **Type**: `input` or `output`
- **Classification**: `trigger` (event-based) or `streaming` (continuous data)
- **Mode**: Determines how the module behaves

#### Module Structure
Each module consists of:
- **Python file**: Main module logic
- **manifest.json**: Module metadata and configuration schema

Example module structure:
```
modules/my_module/
├── my_module.py           # Module implementation
└── manifest.json          # Module definition
```

#### Module Base Class
All modules inherit from `ModuleBase` which provides:
- Configuration management with caching
- Event emission with optimized routing
- Logging with multiple levels
- Lifecycle management (start/stop)
- Strategy pattern support for different behaviors
- Unique instance IDs for tracking

### 2able Input Modules

#### Clock Input (`time_input_trigger`)
- **Purpose**: Time-based triggers and countdown timers
- **Features**: 
  - Target time triggers (HH:MM:SS format)
  - Real-time current time display
  - Countdown timer display
  - Automatic time synchronization
- **Configuration**:
  - `target_time`: Time to trigger at (default:12:00:00)
#### OSC Input (`osc_input_trigger`)
- **Purpose**: Receive OSC messages from external devices
- **Features**:
  - Multiple OSC address patterns
  - Shared server management
  - Automatic port conflict resolution
- **Configuration**:
  - `port`: UDP port to listen on (default: 800  - `address`: OSC address pattern to match

#### Serial Input (`serial_input_trigger`)
- **Purpose**: Receive triggers from serial devices
- **Features**:
  - Configurable baud rate
  - Custom trigger conditions
  - Automatic reconnection
- **Configuration**:
  - `port`: Serial port (e.g.,COM3",/dev/ttyUSB0)
  - `baud_rate`: Communication speed
  - `trigger_condition`: When to trigger

#### Serial Streaming (`serial_input_streaming`)
- **Purpose**: Continuous data from serial devices
- **Features**:
  - Real-time data streaming
  - Configurable data format
  - Automatic parsing

#### sACN Frame Input (`frames_input_trigger`)
- **Purpose**: Receive sACN (Streaming ACN) frame triggers
- **Features**:
  - DMX universe support
  - Frame-based triggering
  - Network configuration

#### sACN Frame Streaming (`frames_input_streaming`)
- **Purpose**: Continuous sACN frame data
- **Features**:
  - Real-time DMX data streaming
  - Multiple universe support

### 3. Available Output Modules

#### Audio Output (`audio_output`)
- **Purpose**: WAV file playback with visualization
- **Features**:
  - WAV file playback with volume control
  - Waveform visualization with caching
  - Concurrent playback support
  - Optimized audio processing
  - Master volume control
- **Configuration**:
  - `file_path`: Path to WAV file
  - `volume`: Individual volume (0-100  - `master_volume`: Global volume control

#### OSC Output (`osc_output`)
- **Purpose**: Send OSC messages to external devices
- **Features**:
  - Adaptive trigger/streaming modes
  - Multiple OSC addresses
  - Auto-detection of input classification
- **Configuration**:
  - `ip_address`: Target IP address
  - `port`: Target UDP port
  - `address`: OSC address pattern

#### DMX Output (`dmx_output`)
- **Purpose**: Control lighting and DMX devices
- **Features**:
  - Multiple protocol support (Serial, Art-Net, sACN)
  - Chase mode for trigger inputs
  - Frame sequencing
  - CSV file support
- **Configuration**:
  - `protocol`: Serial, Art-Net, or sACN
  - `port`: Serial port or network port
  - `csv_file`: Frame data file path

###4ng an Installation

#### Using the Web Interface (Recommended)
1. **Launch the application**: `python main.py`2 **Open browser**: Interface opens automatically at `http://localhost:8000`
3. **Add interactions**: ClickAdd Interaction" button
4. **Configure inputs**: Select input module and configure parameters
5. **Configure outputs**: Select output module and configure parameters
6. **Real-time monitoring**: View module status and performance metrics
7. **Save configuration**: Changes are automatically saved
8. **Module wiki**: Access detailed module documentation

#### Using the Legacy GUI
1. **Launch the application**: `python main.py --gui`
2. **Add interactions**: Use the GUI interface
3. **Configure modules**: Set parameters for inputs and outputs
4. **Test functionality**: Use test buttons or external triggers
5. **Save configuration**: Configuration is automatically saved

#### Configuration Files
- **App Config** (`config/config.json`): Global settings
  - Installation name
  - Master volume
  - Log level
  - Theme preferences

- **Installation Config** (`config/interactions/interactions.json`): Module configurations
  - Input module settings
  - Output module settings
  - Connections between modules

### 5. Real-Time Features

#### WebSocket Communication
- **Real-time updates**: Module status, performance metrics, and events
- **Live clock display**: Current time and countdown updates
- **Performance monitoring**: CPU, memory, and event statistics
- **Module instance tracking**: Unique IDs for proper event routing

#### Performance Optimization
- **Thread pool management**: Optimized concurrent operations
- **Configuration caching**: Intelligent caching with change detection
- **Event routing**: Priority-based routing with batching
- **Audio processing**: Vectorized waveform generation and caching
- **Memory management**: Automatic resource cleanup

## 🔧 Advanced Configuration

### Custom Module Development

1e module directory**: `modules/my_module/`
2. **Implement module class**: Inherit from `ModuleBase`
3. **Create manifest**: Define configuration schema
4. **Test module**: Use web interface to test functionality
5. **Deploy**: Module is automatically discovered

### Network Configuration

#### OSC Communication
- **Default port**:8000Multiple addresses**: Same port, different addresses
- **Port conflicts**: Handled automatically by singleton pattern
- **Testing**: Use included test scripts or external OSC clients

#### Web Interface
- **Default port**: 8000 **CORS support**: Configured for cross-origin requests
- **WebSocket**: Real-time communication for live updates

### Performance Management

#### Performance Levels
- **Maximum**: All optimizations enabled
- **Balanced**: Balanced performance and compatibility (default)
- **Conservative**: Minimal optimizations for stability
- **Disabled**: All optimizations disabled

#### Performance Metrics
- CPU usage
- Memory usage
- Event latency
- Cache hit rates
- Thread pool statistics
- WebSocket connection status

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
- **Cause**: Multiple instances or other applications using port
- **Solution**: Close other instances, change port, or restart system

#### Audio Not Playing
- **Cause**: Missing audio files or incorrect paths
- **Solution**: Check file paths, ensure WAV format, verify volume settings

#### OSC Messages Not Received
- **Cause**: Network issues, incorrect address/port
- **Solution**: Check network connectivity, verify OSC address patterns

#### Web Interface Not Loading
- **Cause**: Backend not running or port conflicts
- **Solution**: Check backend status, verify port80is available

#### Clock Display Not Updating
- **Cause**: WebSocket connection issues or module mapping problems
- **Solution**: Check browser console, verify module instances are running

#### Module Not Loading
- **Cause**: Missing dependencies or invalid manifest
- **Solution**: Check module manifest, ensure all dependencies installed

### Debugging

#### Log Levels
- **No Log**: No output
- **OSC**: Only OSC messages
- **Serial**: Serial communication messages
- **Outputs**: Event triggers and outputs
- **Verbose**: Detailed debugging information

#### Web Interface Debugging
- Check browser console for JavaScript errors
- Verify WebSocket connection status
- Monitor network requests in browser dev tools

#### Performance Debugging
- Use web interface to view performance metrics
- Check thread pool statistics
- Monitor cache hit rates
- View real-time system metrics

## 📚 API Reference

### Backend API Endpoints

#### Configuration
- `GET /config` - Get current configuration
- `POST /config` - Save configuration
- `POST /config/delete_interaction` - Delete specific interaction

#### Module Management
- `GET /modules` - Get available modules
- `GET /module_instances` - Get running module instances
- `GET /modules/{module}/manifest.json` - Get module manifest

#### WebSocket
- `GET /ws/events` - WebSocket endpoint for real-time events

### ModuleBase Class

#### Methods
- `__init__(config, manifest, log_callback, strategy)`: Initialize module
- `start()`: Start module operation
- `stop()`: Stop module operation
- `emit_event(data)`: Emit event to connected modules
- `handle_event(data)`: Handle incoming events
- `update_config(new_config)`: Update module configuration

#### Properties
- `config`: Module configuration dictionary
- `manifest`: Module manifest dictionary
- `log_callback`: Logging function
- `strategy`: Module behavior strategy
- `instance_id`: Unique instance identifier

### Event System

#### Event Format
```python
[object Object]  instance_id: que-id",  # Module instance identifieraddress":/trigger",       # OSC address (for OSC events)
    argsvalue"],           # Event arguments
  trigger: 0.75          # Custom event data
   current_time": "19,  # Clock events
   countdown:20:29,# Countdown events
    # ... additional fields
}
```

#### Event Flow
1. Input module receives trigger
2. Input module emits event with instance_id
3. Optimized message router routes event
4. Output module receives event
5. Output module generates response

## 🤝 Contributing

### Development Guidelines
1llow existing code structure
2. Add comprehensive logging
3. Include manifest files for modules
4 thoroughly before submitting
5. Update documentation
6 performance optimizations where appropriate
7. Ensure WebSocket compatibility for real-time features

### Module Development1herit from `ModuleBase`
2. Implement required methods
3eate manifest file
4. Add error handling
5Include cleanup in `stop()` method
6. Use strategy patterns for different behaviors
7. Implement performance monitoring
8. Add real-time event emission for UI updates

### Frontend Development1se React with TypeScript
2existing component patterns
3. Implement proper error handling
4. Add loading states for async operations
5. Use WebSocket for real-time updates
6. Maintain responsive design

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Python OSC library for network communication
- Pygame for audio playback
- FastAPI for web backend
- React for web frontend
- Pydub for audio processing
- Matplotlib for waveform generation
- sACN library for DMX over network
- PySerial for serial communication

---

For more information, see the individual module documentation in the web interface wiki section.