"""
pytest configuration file for Interaction Framework tests.
Contains fixtures and setup for testing the web application and modules.
"""

import pytest
import asyncio
import subprocess
import time
import signal
import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Dict, Any
import httpx
from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from main import InteractionApp


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config_dir():
    """Create a temporary configuration directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="interaction_test_")
    config_dir = Path(temp_dir) / "config"
    config_dir.mkdir()
    
    # Create test config files
    (config_dir / "config.json").write_text(json.dumps({
        "installation_name": "Test Installation",
        "theme": "dark",
        "version": "1.0.0",
        "master_volume": 50.0,
        "log_level": "Debug"
    }))
    
    interactions_dir = config_dir / "interactions"
    interactions_dir.mkdir()
    (interactions_dir / "interactions.json").write_text(json.dumps({
        "interactions": []
    }))
    
    yield config_dir
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
async def app_server(test_config_dir):
    """Start the Interaction app server for testing."""
    # Set environment variables for testing
    os.environ['INTERACTION_CONFIG_DIR'] = str(test_config_dir.parent)
    
    # Start the server process
    server_process = subprocess.Popen([
        sys.executable, "main.py", "--no-browser", "--port", "8899"
    ], cwd=Path(__file__).parent.parent)
    
    # Wait for server to start
    for _ in range(30):  # Wait up to 30 seconds
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8899/", timeout=1.0)
                if response.status_code == 200:
                    break
        except:
            await asyncio.sleep(1)
    else:
        server_process.terminate()
        raise RuntimeError("Server failed to start")
    
    yield "http://localhost:8899"
    
    # Cleanup: Stop the server
    server_process.terminate()
    server_process.wait(timeout=10)


@pytest.fixture(scope="session")
async def browser():
    """Create a browser instance for testing."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest.fixture
async def browser_context(browser: Browser):
    """Create a new browser context for each test."""
    context = await browser.new_context(
        viewport={"width": 1280, "height": 720},
        ignore_https_errors=True,
    )
    yield context
    await context.close()


@pytest.fixture
async def page(browser_context: BrowserContext):
    """Create a new page for each test."""
    page = await browser_context.new_page()
    yield page
    await page.close()


@pytest.fixture
async def http_client():
    """Create an HTTP client for API testing."""
    async with httpx.AsyncClient() as client:
        yield client


@pytest.fixture
def sample_audio_file(test_config_dir):
    """Create a sample audio file for testing."""
    audio_dir = test_config_dir.parent / "audio"
    audio_dir.mkdir(exist_ok=True)
    
    # Create a minimal WAV file (just headers, no actual audio data)
    sample_file = audio_dir / "test_audio.wav"
    with open(sample_file, "wb") as f:
        # WAV file header (44 bytes)
        f.write(b'RIFF\x24\x08\x00\x00WAVE')  # RIFF header
        f.write(b'fmt \x10\x00\x00\x00\x01\x00\x01\x00')  # fmt chunk
        f.write(b'\x44\xac\x00\x00\x88\x58\x01\x00\x02\x00\x10\x00')  # format data
        f.write(b'data\x00\x08\x00\x00')  # data chunk header
        f.write(b'\x00' * 2048)  # silent audio data
    
    yield sample_file
    
    # Cleanup
    if sample_file.exists():
        sample_file.unlink()


@pytest.fixture
def sample_interaction():
    """Create a sample interaction configuration."""
    return {
        "input": {
            "module": "osc_input_trigger",
            "config": {
                "listen_address": "127.0.0.1",
                "listen_port": 8000,
                "message_address": "/test"
            }
        },
        "output": {
            "module": "audio_output",
            "config": {
                "file_path": "test_audio.wav",
                "volume": 50.0
            }
        }
    }


@pytest.fixture
def mock_modules():
    """Mock module list for testing."""
    return [
        {
            "id": "osc_input_trigger",
            "name": "OSC Input Trigger",
            "type": "input",
            "description": "Receives OSC messages as triggers"
        },
        {
            "id": "audio_output",
            "name": "Audio Output",
            "type": "output", 
            "description": "Plays audio files"
        },
        {
            "id": "dmx_output",
            "name": "DMX Output",
            "type": "output",
            "description": "Controls DMX lighting"
        }
    ]


@pytest.fixture
def performance_metrics():
    """Sample performance metrics for testing."""
    return {
        "timestamp": time.time(),
        "cpu_usage": 45.2,
        "memory_usage": 62.8,
        "thread_count": 12,
        "cache_hit_rate": 0.85,
        "event_latency": 0.005,
        "events_per_second": 150
    }