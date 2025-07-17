# Interaction - Interactive Art Installation Framework

A modular Python framework for creating interactive art installations using microservices that communicate over OSC (Open Sound Control). This system allows you to build complex interactive experiences by connecting input modules (sensors, triggers, etc.) to output modules (audio, video, lighting, etc.) through a visual GUI.

## 🏗️ Architecture Overview

### Microservice Design
The Interaction framework uses a microservice architecture where each component is a self-contained module:

- **Input Modules**: Handle external triggers (OSC messages, sensors, buttons, etc.)
- **Output Modules**: Generate responses (audio playback, video, lighting, etc.)
- **Message Router**: Routes events between input and output modules with optimized performance
- **Module Loader**: Dynamically discovers and loads modules with integrated caching
- **GUI**: Visual interface for configuring and managing installations

### Core Components

```
Interaction/
├── main.py                 # Application entry point with performance management
├── gui.py                  # Main GUI interface for configuration
├── message_router.py       # Optimized event routing system
├── module_loader.py        # Module discovery with thread pool and config cache
├── modules/                # Module definitions
│   ├── module_base.py      # Base class for all modules with strategy patterns
│   ├── audio_output/       # Audio playback with optimized processing
│   ├── osc_output/         # Unified OSC output (trigger/streaming adaptive)
│   ├── dmx_output/         # Unified DMX output (trigger/streaming adaptive)
│   └── osc_input_trigger/  # OSC message receiver
├── config/                 # Configuration files
│   ├── config.json         # App-level settings
│   └── interactions/       # Installation configurations
├── web-frontend/           # Web-based interface
└── tests/                  # Test assets and scripts
```

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required packages (see `requirements.txt`):
  - `tkinter` (usually included with Python)
  - `pythonosc` (OSC communication)
  - `pygame` (audio playback)
  - `pydub` (audio processing)
  - `matplotlib` (waveform generation)
  - `Pillow` (image processing)
  - `fastapi` (web backend)
  - `uvicorn` (web server)

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application:
   - **GUI Mode**: `python main.py --gui`
   - **Web Mode**: `python main.py --web` (default)
   - **Startup Script**: `python start_web_gui.py`

## 📋 How to Build an Installation

### 1. Understanding the Module System

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

### 2. Creating Input Modules

Input modules receive external triggers and emit events. Example:

```python
from modules.module_base import ModuleBase, TriggerStrategy

class MyInputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        self.trigger_value = config.get("trigger_value", 0.5)
    
    def start(self):
        """Initialize the input source"""
        # Set up your input (sensor, network, etc.)
        pass
    
    def stop(self):
        """Clean up resources"""
        # Clean up your input
        pass
    
    def _on_trigger(self, value):
        """Handle input trigger"""
        if value > self.trigger_value:
            self.emit_event({"trigger": value})
```

#### Input Module Manifest
```json
{
    "name": "My Input",
    "type": "input",
    "classification": "trigger",
    "description": "Custom input module",
    "fields": [
        {
            "name": "trigger_value",
            "type": "number",
            "default": 0.5,
            "label": "Trigger Threshold",
            "description": "Trigger threshold value"
        }
    ]
}
```

### 3. Creating Output Modules

Output modules receive events and generate responses. Example:

```python
from modules.module_base import ModuleBase, TriggerStrategy

class MyOutputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        self.response_type = config.get("response_type", "default")
    
    def start(self):
        """Initialize the output system"""
        # Set up your output (audio, video, etc.)
        pass
    
    def stop(self):
        """Clean up resources"""
        # Clean up your output
        pass
    
    def handle_event(self, data):
        """Handle incoming events"""
        trigger_value = data.get("trigger", 0)
        self.log_message(f"Responding to trigger: {trigger_value}")
        # Generate your response
```

#### Output Module Manifest
```json
{
    "name": "My Output",
    "type": "output",
    "classification": "trigger",
    "description": "Custom output module",
    "fields": [
        {
            "name": "response_type",
            "type": "text",
            "default": "default",
            "label": "Response Type",
            "description": "Type of response to generate"
        }
    ]
}
```

### 4. Configuring an Installation

#### Using the GUI
1. **Launch the application**: `python main.py --gui`
2. **Add interactions**: Click "+ Add Interaction"
3. **Configure inputs**: Select input module and configure parameters
4. **Configure outputs**: Select output module and configure parameters
5. **Connect modules**: The system automatically connects input to output
6. **Test**: Use the test buttons or external triggers
7. **Save**: Configuration is automatically saved

#### Using the Web Interface
1. **Launch the application**: `python main.py --web`
2. **Open browser**: Interface opens automatically
3. **Configure modules**: Use the web-based interface
4. **Real-time monitoring**: View module status and performance
5. **Wiki documentation**: Access module documentation

#### Configuration Files
- **App Config** (`config/config.json`): Global settings
  - Installation name
  - Master volume
  - Log level
  - Theme

- **Installation Config** (`config/interactions/interactions.json`): Module configurations
  - Input module settings
  - Output module settings
  - Connections between modules

### 5. OSC Communication

#### OSC Input Module
The OSC input module listens for OSC messages and converts them to events:

```python
# OSC message format
/trigger 0.75    # Triggers with value 0.75
/play "test"     # Triggers with string "test"
```

#### OSC Output Module (Unified)
The unified OSC output module adapts to connected input types:
- **Trigger Mode**: Sends single OSC messages on events
- **Streaming Mode**: Sends continuous OSC data streams
- **Auto-detection**: Automatically switches based on input classification

#### OSC Configuration
- **Port**: UDP port to listen on (default: 8000)
- **Address**: OSC address pattern to match (e.g., `/trigger`, `/play`)
- **IP Address**: Target IP for output (default: localhost)

#### Testing OSC
Use the included test scripts or external OSC clients:
```bash
# Send test OSC messages
python tests/Scripts/osc_test.py
```

### 6. Audio Output Module

The audio output module provides:
- **File playback**: Play WAV files with optimized processing
- **Volume control**: Individual and master volume
- **Waveform visualization**: Visual representation of audio with caching
- **Concurrent playback**: Multiple audio files simultaneously
- **Performance optimization**: Vectorized audio processing

#### Audio Configuration
- **File path**: Path to WAV file
- **Volume**: Individual volume (0-100%)
- **Master volume**: Global volume control in GUI

### 7. DMX Output Module (Unified)

The unified DMX output module supports multiple protocols:
- **Serial DMX**: Direct serial communication
- **Art-Net**: Network-based DMX over UDP
- **sACN**: Streaming ACN protocol
- **Chase Mode**: Automatic frame sequencing for trigger inputs

#### DMX Configuration
- **Protocol**: Serial, Art-Net, or sACN
- **Serial Port**: COM port for serial DMX
- **IP Address**: Target IP for network protocols
- **FPS**: Frames per second for chase mode
- **CSV File**: Frame data file path

## 📁 File Structure Deep Dive

### Core Application Files

#### `main.py`
- **Purpose**: Application entry point with performance management
- **Key Features**:
  - Prevents multiple instances from running
  - Creates lock file for process management
  - Handles graceful shutdown
  - Initializes performance optimizations
  - Loads GUI or web interface

#### `gui.py`
- **Purpose**: Main graphical interface
- **Key Components**:
  - `InteractionGUI`: Main application window
  - `InteractionBlock`: Individual input/output configuration
  - `Logger`: Logging system with multiple verbosity levels
  - `EditableLabel`: Inline editable text fields

#### `message_router.py`
- **Purpose**: Optimized event routing system
- **Key Features**:
  - Priority-based event routing
  - Batched event processing
  - Lock-free data structures
  - Performance monitoring
  - Weak reference management

#### `module_loader.py`
- **Purpose**: Module discovery with integrated performance features
- **Key Features**:
  - Automatic module discovery
  - Manifest validation
  - Module instantiation
  - Thread pool management
  - Configuration caching
  - Factory pattern implementation

### Module System

#### `modules/module_base.py`
- **Purpose**: Base class for all modules with strategy patterns
- **Key Features**:
  - Configuration management with caching
  - Event emission with optimized routing
  - Logging interface
  - Lifecycle hooks
  - Strategy pattern support
  - State management

#### `modules/osc_input_trigger/`
- **Purpose**: OSC message receiver
- **Key Components**:
  - `osc_input.py`: Main OSC input module
  - `osc_server_manager.py`: Shared OSC server management
  - `manifest.json`: Module definition

#### `modules/audio_output/`
- **Purpose**: Audio playback system with optimizations
- **Key Features**:
  - WAV file playback
  - Volume control
  - Optimized waveform generation
  - Concurrent audio support
  - Performance monitoring

#### `modules/osc_output/`
- **Purpose**: Unified OSC output system
- **Key Features**:
  - Adaptive trigger/streaming modes
  - Auto-detection of input classification
  - Multiple OSC address support
  - Performance optimization

#### `modules/dmx_output/`
- **Purpose**: Unified DMX output system
- **Key Features**:
  - Multiple protocol support (Serial, Art-Net, sACN)
  - Chase mode for trigger inputs
  - Frame sequencing
  - Performance optimization

### Configuration System

#### `config/config.json`
- **Purpose**: Application-level settings
- **Settings**:
  - Installation name
  - Master volume
  - Log level
  - Theme preferences

#### `config/interactions/interactions.json`
- **Purpose**: Installation configuration
- **Structure**:
  - Array of interaction blocks
  - Input module configurations
  - Output module configurations
  - Connection mappings

### Web Interface

#### `web-frontend/`
- **Purpose**: Web-based user interface
- **Key Features**:
  - Real-time module monitoring
  - Configuration interface
  - Wiki documentation system
  - Performance metrics display

### Test Assets

#### `tests/Assets/`
- **Purpose**: Test audio files and resources
- **Contents**:
  - Sample WAV files for testing
  - Generated waveform images

#### `tests/Scripts/`
- **Purpose**: Testing and debugging tools
- **Scripts**:
  - `osc_test.py`: OSC message testing
  - Additional test utilities

## 🔧 Advanced Configuration

### Custom Module Development

1. **Create module directory**: `modules/my_module/`
2. **Implement module class**: Inherit from `ModuleBase`
3. **Create manifest**: Define configuration schema
4. **Test module**: Use GUI to test functionality
5. **Deploy**: Module is automatically discovered

### Network Configuration

#### OSC Ports
- **Default port**: 8000
- **Multiple addresses**: Same port, different addresses
- **Port conflicts**: Handled automatically by singleton pattern

#### IP Address
- **Local IP**: Automatically detected and displayed
- **Network access**: Bind to 0.0.0.0 for network access
- **Firewall**: Ensure UDP ports are open

### Performance Optimization

#### Integrated Performance Features
- **Thread Pool**: Optimized thread management for concurrent operations
- **Configuration Cache**: Intelligent caching with change detection
- **Message Router**: Priority-based event routing with batching
- **Audio Processing**: Vectorized waveform generation and caching
- **Performance Monitoring**: Real-time metrics and auto-adjustment

#### Audio Performance
- **Concurrent playback**: Uses pygame mixer channels
- **Memory management**: Automatic cleanup of audio resources
- **Waveform caching**: Generated waveforms are cached
- **Vectorized processing**: Optimized audio operations

#### OSC Performance
- **Shared servers**: Multiple modules share OSC servers
- **Efficient routing**: Direct callback execution
- **Resource cleanup**: Automatic server shutdown

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

#### Module Not Loading
- **Cause**: Missing dependencies or invalid manifest
- **Solution**: Check module manifest, ensure all dependencies installed

#### Performance Issues
- **Cause**: High CPU/memory usage
- **Solution**: Check performance metrics in web interface, adjust optimization levels

### Debugging

#### Log Levels
- **No Log**: No output
- **OSC**: Only OSC messages
- **Serial**: Serial communication messages
- **Outputs**: Event triggers and outputs
- **Verbose**: Detailed debugging information

#### OSC Debugging
- Use test scripts to verify OSC communication
- Check server status in GUI
- Monitor network traffic

#### Performance Debugging
- Use web interface to view performance metrics
- Check thread pool statistics
- Monitor cache hit rates

## 📚 API Reference

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

### Event System

#### Event Format
```python
{
    "address": "/trigger",      # OSC address (for OSC events)
    "args": ["value"],          # Event arguments
    "trigger": 0.75,           # Custom event data
    # ... additional fields
}
```

#### Event Flow
1. Input module receives trigger
2. Input module emits event
3. Optimized message router routes event
4. Output module receives event
5. Output module generates response

### Performance Management

#### Performance Levels
- **Maximum**: All optimizations enabled
- **Balanced**: Balanced performance and compatibility
- **Conservative**: Minimal optimizations for stability
- **Disabled**: All optimizations disabled

#### Performance Metrics
- CPU usage
- Memory usage
- Event latency
- Cache hit rates
- Thread pool statistics

## 🤝 Contributing

### Development Guidelines
1. Follow existing code structure
2. Add comprehensive logging
3. Include manifest files for modules
4. Test thoroughly before submitting
5. Update documentation
6. Use performance optimizations where appropriate

### Module Development
1. Inherit from `ModuleBase`
2. Implement required methods
3. Create manifest file
4. Add error handling
5. Include cleanup in `stop()` method
6. Use strategy patterns for different behaviors
7. Implement performance monitoring

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Python OSC library for network communication
- Pygame for audio playback
- Tkinter for GUI framework
- Pydub for audio processing
- Matplotlib for waveform generation
- FastAPI for web backend
- Uvicorn for web server

---

For more information, see the individual module documentation and test scripts.

## Developer Guide: Extending the Event-Driven Modular GUI

1. **Architectural Overview**: Event-driven, state-driven, thread-safe design. No polling. All state changes via explicit pathways.
2. **Adding a New Module**:
   - **Manifest**: Define fields, types, and protocol-dependent options.
   - **Module Class**: Inherit from ModuleBase, implement event/callback system, emit events for all state changes.
   - **GUI Integration**: Use event/callbacks for all dynamic fields. Never use polling. Register any threads with the GUI (self.gui_ref.threads.append(...)).
   - **Config**: All config/state changes must go through explicit update pathways. Use get_input_config/get_output_config and update_config methods.
   - **Thread Safety**: All GUI updates from threads must use self.root.after().
   - **Shutdown**: Implement stop() for all background tasks. Register threads for clean shutdown.
   - **Performance**: Use integrated thread pool and caching systems.
3. **Best Practices**:
   - Centralize state in config and block objects.
   - Only save/load config on explicit state changes.
   - Use clear docstrings and comments for AI and human maintainers.
   - Add TODOs for any future improvements or places where new modules should follow the same patterns.
   - Implement strategy patterns for different module behaviors.
4. **AI/Automation Notes**:
   - All module and GUI logic is discoverable via clear method names and docstrings.
   - All event/callback registration points are explicit.
   - Thread and resource management is centralized for easy auditing.
   - No polling or hidden background tasks: all state changes are explicit and traceable.
   - Performance optimizations are integrated and configurable.
5. **Example Checklist for New Modules**:
   - [ ] Manifest defines all fields and protocol options
   - [ ] Module emits events for all state changes
   - [ ] GUI fields update only via event/callbacks
   - [ ] No polling or untracked threads
   - [ ] All threads registered for shutdown
   - [ ] All config/state changes go through explicit update pathways
   - [ ] stop() implemented for all background tasks
   - [ ] All GUI updates from threads use self.root.after()
   - [ ] Docstrings and comments added for AI/human maintainers
   - [ ] TODOs left for future improvements
   - [ ] Performance optimizations implemented where appropriate
   - [ ] Strategy patterns used for different behaviors

Make this section clear, concise, and actionable for both AI and human developers.