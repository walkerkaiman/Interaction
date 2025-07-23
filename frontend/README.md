# Interactive Art Installation - Web GUI

A simple web-based interface for the Interactive Art Installation Framework that replaces the old Tkinter GUI.

## Quick Start

1. **Start everything with one command:**
   ```bash
   python main.py --web
   ```
   This will automatically:
   - Start the backend server
   - Open the web interface in your browser
   - Show connection status

2. **Or use the convenience script:**
   ```bash
   python start_web_gui.py
   ```

3. **Manual start (if needed):**
   ```bash
   # Start the backend only
   python main.py --web
   
   # Then manually open in your browser:
   # file:///path/to/your/project/web-frontend/simple-gui.html
   ```

## Features

The web interface provides the same functionality as the old Tkinter GUI:

### Dashboard
- Overview of all available modules
- Connection status to backend

### Modules
- View all available input and output modules
- See module descriptions and classifications

### Interactions
- Create connections between input and output modules
- View existing interactions
- Remove interactions

### Events
- Real-time event monitoring via WebSocket
- Live log of all system events

### Configuration
- Save and load installation configuration
- Set installation name

## How It Works

- **Backend**: FastAPI server running on `http://localhost:8000`
- **Frontend**: Simple HTML/JavaScript page that connects to the backend
- **Real-time**: WebSocket connection for live event updates

## Troubleshooting

- **Connection issues**: Make sure the backend is running on port 8000
- **CORS errors**: The backend is configured to allow all origins for local development
- **WebSocket not connecting**: Check that the backend WebSocket endpoint is working

## File Structure

```
web-frontend/
├── simple-gui.html    # Main web interface
├── README.md         # This file
└── ...               # Other React files (not used by simple GUI)
```

The simple GUI is a single HTML file that contains everything needed to interact with your backend!
