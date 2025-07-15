# Interaction - Interactive Art Installation Framework

A modular Python framework for creating interactive art installations using microservices that communicate over OSC (Open Sound Control). This system allows you to build complex interactive experiences by connecting input modules (sensors, triggers, etc.) to output modules (audio, video, lighting, etc.) through a visual GUI.

## 🏗️ Architecture Overview

### Microservice Design
The Interaction framework uses a microservice architecture where each component is a self-contained module:

- **Input Modules**: Handle external triggers (OSC messages, sensors, buttons, etc.)
- **Output Modules**: Generate responses (audio playback, video, lighting, etc.)
- **Message Router**: Routes events between input and output modules
- **Module Loader**: Dynamically discovers and loads modules
- **GUI**: Visual interface for configuring and managing installations

### Core Components

```
Interaction/
├── main.py                 # Application entry point with singleton protection
├── gui.py                  # Main GUI interface for configuration
├── message_router.py       # Routes events between modules
├── module_loader.py        # Discovers and loads modules dynamically
├── modules/                # Module definitions
│   ├── module_base.py      # Base class for all modules
│   ├── audio_output/       # Audio playback module
│   └── osc_input/          # OSC message receiver module
├── config/                 # Configuration files
│   ├── config.json         # App-level settings
│   └── interactions/       # Installation configurations
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

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python main.py`

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
- Configuration management
- Event emission
- Logging
- Lifecycle management (start/stop)

### 2. Creating Input Modules

Input modules receive external triggers and emit events. Example:

```python
from modules.module_base import ModuleBase

class MyInputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
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
    "description": "Custom input module",
    "config_schema": {
        "trigger_value": {
            "type": "number",
            "default": 0.5,
            "description": "Trigger threshold"
        }
    }
}
```

### 3. Creating Output Modules

Output modules receive events and generate responses. Example:

```python
from modules.module_base import ModuleBase

class MyOutputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
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
    "description": "Custom output module",
    "config_schema": {
        "response_type": {
            "type": "string",
            "default": "default",
            "description": "Type of response to generate"
        }
    }
}
```

### 4. Configuring an Installation

#### Using the GUI
1. **Launch the application**: `python main.py`
2. **Add interactions**: Click "+ Add Interaction"
3. **Configure inputs**: Select input module and configure parameters
4. **Configure outputs**: Select output module and configure parameters
5. **Connect modules**: The system automatically connects input to output
6. **Test**: Use the test buttons or external triggers
7. **Save**: Configuration is automatically saved

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

#### OSC Configuration
- **Port**: UDP port to listen on (default: 8000)
- **Address**: OSC address pattern to match (e.g., `/trigger`, `/play`)

#### Testing OSC
Use the included test scripts or external OSC clients:
```bash
# Send test OSC messages
python tests/Scripts/osc_test.py
```

### 6. Audio Output Module

The audio output module provides:
- **File playback**: Play WAV files
- **Volume control**: Individual and master volume
- **Waveform visualization**: Visual representation of audio
- **Concurrent playback**: Multiple audio files simultaneously

#### Audio Configuration
- **File path**: Path to WAV file
- **Volume**: Individual volume (0-100%)
- **Master volume**: Global volume control in GUI

## 📁 File Structure Deep Dive

### Core Application Files

#### `main.py`
- **Purpose**: Application entry point with singleton protection
- **Key Features**:
  - Prevents multiple instances from running
  - Creates lock file for process management
  - Handles graceful shutdown
  - Loads GUI

#### `gui.py`
- **Purpose**: Main graphical interface
- **Key Components**:
  - `InteractionGUI`: Main application window
  - `InteractionBlock`: Individual input/output configuration
  - `Logger`: Logging system with multiple verbosity levels
  - `EditableLabel`: Inline editable text fields

#### `message_router.py`
- **Purpose**: Routes events between modules
- **Key Features**:
  - Dynamic event routing
  - Event filtering
  - Callback management

#### `module_loader.py`
- **Purpose**: Discovers and loads modules dynamically
- **Key Features**:
  - Automatic module discovery
  - Manifest validation
  - Module instantiation

### Module System

#### `modules/module_base.py`
- **Purpose**: Base class for all modules
- **Key Features**:
  - Configuration management
  - Event emission
  - Logging interface
  - Lifecycle hooks

#### `modules/osc_input/`
- **Purpose**: OSC message receiver
- **Key Components**:
  - `osc_input.py`: Main OSC input module
  - `osc_server_manager.py`: Shared OSC server management
  - `manifest.json`: Module definition

#### `modules/audio_output/`
- **Purpose**: Audio playback system
- **Key Features**:
  - WAV file playback
  - Volume control
  - Waveform generation
  - Concurrent audio support

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

#### Audio Performance
- **Concurrent playback**: Uses pygame mixer channels
- **Memory management**: Automatic cleanup of audio resources
- **Waveform caching**: Generated waveforms are cached

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

### Debugging

#### Log Levels
- **No Log**: No output
- **Only Output Triggers**: Only event triggers
- **Show Mode**: Normal operation messages
- **Verbose**: Detailed debugging information

#### OSC Debugging
- Use test scripts to verify OSC communication
- Check server status in GUI
- Monitor network traffic

## 📚 API Reference

### ModuleBase Class

#### Methods
- `__init__(config, manifest, log_callback)`: Initialize module
- `start()`: Start module operation
- `stop()`: Stop module operation
- `emit_event(data)`: Emit event to connected modules
- `handle_event(data)`: Handle incoming events
- `update_config(new_config)`: Update module configuration

#### Properties
- `config`: Module configuration dictionary
- `manifest`: Module manifest dictionary
- `log_callback`: Logging function

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
3. Message router routes event
4. Output module receives event
5. Output module generates response

## 🤝 Contributing

### Development Guidelines
1. Follow existing code structure
2. Add comprehensive logging
3. Include manifest files for modules
4. Test thoroughly before submitting
5. Update documentation

### Module Development
1. Inherit from `ModuleBase`
2. Implement required methods
3. Create manifest file
4. Add error handling
5. Include cleanup in `stop()` method

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Python OSC library for network communication
- Pygame for audio playback
- Tkinter for GUI framework
- Pydub for audio processing
- Matplotlib for waveform generation

---

For more information, see the individual module documentation and test scripts.

## Developer Guide: Extending the Event-Driven Modular GUI

1. Architectural Overview: Event-driven, state-driven, thread-safe design. No polling. All state changes via explicit pathways.
2. Adding a New Module:
   - Manifest: Define fields, types, and protocol-dependent options.
   - Module Class: Inherit from ModuleBase, implement event/callback system, emit events for all state changes.
   - GUI Integration: Use event/callbacks for all dynamic fields. Never use polling. Register any threads with the GUI (self.gui_ref.threads.append(...)).
   - Config: All config/state changes must go through explicit update pathways. Use get_input_config/get_output_config and update_config methods.
   - Thread Safety: All GUI updates from threads must use self.root.after().
   - Shutdown: Implement stop() for all background tasks. Register threads for clean shutdown.
3. Best Practices:
   - Centralize state in config and block objects.
   - Only save/load config on explicit state changes.
   - Use clear docstrings and comments for AI and human maintainers.
   - Add TODOs for any future improvements or places where new modules should follow the same patterns.
4. AI/Automation Notes:
   - All module and GUI logic is discoverable via clear method names and docstrings.
   - All event/callback registration points are explicit.
   - Thread and resource management is centralized for easy auditing.
   - No polling or hidden background tasks: all state changes are explicit and traceable.
5. Example Checklist for New Modules:
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

Make this section clear, concise, and actionable for both AI and human developers.