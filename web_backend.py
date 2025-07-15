from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import threading
import json
from module_loader import ModuleLoader
from message_router import EventRouter

app = FastAPI()

# Allow CORS for local network access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared loader and event router
loader = ModuleLoader()
event_router = EventRouter()

# --- REST Endpoints ---

@app.get("/modules")
def list_modules():
    """List all available modules and their manifests."""
    return loader.get_available_modules()

@app.get("/modules/{module_name}")
def get_module_manifest(module_name: str):
    manifest = loader.load_manifest(module_name)
    if not manifest:
        return JSONResponse(status_code=404, content={"error": "Module not found"})
    return manifest

# Factory pattern: module creation is now routed through ModuleLoader's factory system
@app.post("/modules/{module_name}/instance")
def create_module_instance(module_name: str, config: dict):
    instance = loader.create_module_instance(module_name, config)
    if not instance:
        return JSONResponse(status_code=400, content={"error": "Failed to create module instance"})
    return {"status": "created", "module": module_name}

@app.get("/state")
def get_state():
    """Get current state of all modules and connections."""
    return {
        "modules": loader.get_available_modules(),
        "connections": event_router.get_connections(),
        "states": event_router.get_all_states(),
    }

@app.get("/config")
def get_config():
    try:
        with open("config/interactions/interactions.json", "r") as f:
            return json.load(f)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/config")
def save_config(config: dict):
    try:
        with open("config/interactions/interactions.json", "w") as f:
            json.dump(config, f, indent=2)
        return {"status": "saved"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- WebSocket for Real-Time Events ---

clients = set()

def event_broadcast_loop():
    # This is a placeholder for a real event subscription system
    # In production, you would subscribe to the EventRouter and push events to clients
    pass

@app.websocket("/ws/events")
async def websocket_events(ws: WebSocket):
    await ws.accept()
    clients.add(ws)
    try:
        while True:
            # In a real system, push events from the event router
            data = await ws.receive_text()
            # Echo for now
            await ws.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        clients.remove(ws)

# --- Run function for main.py ---
def run():
    # Optionally start event broadcast thread here
    uvicorn.run("web_backend:app", host="0.0.0.0", port=8000, reload=False) 