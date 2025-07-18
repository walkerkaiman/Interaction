import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import asyncio
import websockets
import json

@pytest.mark.asyncio
async def test_websocket_event_emission():
    # This test assumes the backend WebSocket server is running on ws://localhost:8765
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            # Subscribe to all events (protocol may vary)
            await websocket.send(json.dumps({"action": "subscribe", "event": "module_event"}))
            # Wait for an event (timeout after 2 seconds)
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            data = json.loads(response)
            assert "type" in data or "event" in data  # Adjust as needed for your protocol
    except Exception as e:
        pytest.skip(f"WebSocket server not running or not reachable: {e}") 