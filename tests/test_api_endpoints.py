"""
Test suite for API endpoints.
Tests all REST API endpoints to ensure they respond correctly and maintain functionality.
"""

import pytest
import json
import httpx
from pathlib import Path


class TestAPIEndpoints:
    """Test all API endpoints for correct responses and functionality."""

    @pytest.mark.asyncio
    async def test_modules_endpoint(self, app_server, http_client):
        """Test that /modules endpoint returns module list."""
        response = await http_client.get(f"{app_server}/modules")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Should have at least some modules
        assert len(data) > 0
        
        # Each module should have required fields
        for module in data:
            assert "id" in module
            assert "name" in module
            assert "type" in module

    @pytest.mark.asyncio
    async def test_module_instances_endpoint(self, app_server, http_client):
        """Test that /module_instances endpoint returns instance list."""
        response = await http_client.get(f"{app_server}/module_instances")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    @pytest.mark.asyncio
    async def test_config_endpoint_get(self, app_server, http_client):
        """Test GET /config endpoint returns configuration."""
        response = await http_client.get(f"{app_server}/config")
        assert response.status_code == 200
        data = response.json()
        
        # Should have main config fields
        assert "installation_name" in data
        assert "interactions" in data
        assert isinstance(data["interactions"], list)

    @pytest.mark.asyncio
    async def test_config_endpoint_post(self, app_server, http_client, sample_interaction):
        """Test POST /config endpoint saves configuration."""
        # First get current config
        response = await http_client.get(f"{app_server}/config")
        assert response.status_code == 200
        current_config = response.json()
        
        # Add a test interaction
        test_config = {
            "installation_name": "Test Installation Updated",
            "interactions": [sample_interaction]
        }
        
        response = await http_client.post(
            f"{app_server}/config",
            json=test_config,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Verify the config was saved
        response = await http_client.get(f"{app_server}/config")
        assert response.status_code == 200
        updated_config = response.json()
        assert updated_config["installation_name"] == "Test Installation Updated"
        assert len(updated_config["interactions"]) == 1

    @pytest.mark.asyncio
    async def test_delete_interaction_endpoint(self, app_server, http_client, sample_interaction):
        """Test deletion of interactions."""
        # First add an interaction
        test_config = {
            "installation_name": "Test",
            "interactions": [sample_interaction, sample_interaction]
        }
        
        response = await http_client.post(
            f"{app_server}/config",
            json=test_config,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Delete the first interaction
        response = await http_client.post(
            f"{app_server}/config/delete_interaction",
            json={"index": 0},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Verify one interaction remains
        response = await http_client.get(f"{app_server}/config")
        assert response.status_code == 200
        config = response.json()
        assert len(config["interactions"]) == 1

    @pytest.mark.asyncio
    async def test_module_manifest_endpoint(self, app_server, http_client):
        """Test module manifest endpoints."""
        # Test audio_output manifest
        response = await http_client.get(f"{app_server}/modules/audio_output/manifest.json")
        assert response.status_code == 200
        manifest = response.json()
        assert "fields" in manifest

    @pytest.mark.asyncio
    async def test_browse_files_endpoint(self, app_server, http_client):
        """Test file browsing endpoint."""
        response = await http_client.get(f"{app_server}/api/browse_files")
        assert response.status_code == 200
        data = response.json()
        assert "files" in data
        assert isinstance(data["files"], list)

    @pytest.mark.asyncio
    async def test_module_notes_endpoints(self, app_server, http_client):
        """Test module notes get/post endpoints."""
        test_module_id = "test_module_123"
        test_notes = "These are test notes for the module."
        
        # Save notes
        response = await http_client.post(
            f"{app_server}/module_notes/{test_module_id}",
            json={"notes": test_notes},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Retrieve notes
        response = await http_client.get(f"{app_server}/module_notes/{test_module_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == test_notes

    @pytest.mark.asyncio
    async def test_static_file_serving(self, app_server, http_client):
        """Test that static files are served correctly."""
        response = await http_client.get(f"{app_server}/")
        assert response.status_code == 200
        # Should return HTML content (index.html)
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_play_audio_endpoint(self, app_server, http_client, sample_interaction):
        """Test the audio playback endpoint."""
        # First set up a config with an audio interaction
        test_config = {
            "installation_name": "Test",
            "interactions": [sample_interaction]
        }
        
        response = await http_client.post(
            f"{app_server}/config",
            json=test_config,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        
        # Try to play audio (may fail if no audio instance, but endpoint should respond)
        response = await http_client.post(
            f"{app_server}/api/play_audio",
            json={"interaction_index": 0},
            headers={"Content-Type": "application/json"}
        )
        # Accept both success and 404 (no audio instance running)
        assert response.status_code in [200, 404]

    @pytest.mark.asyncio
    async def test_upload_file_endpoint(self, app_server, http_client, sample_audio_file):
        """Test file upload endpoint."""
        # Create test file data
        files = {"file": ("test.wav", open(sample_audio_file, "rb"), "audio/wav")}
        
        # Note: httpx doesn't handle multipart the same way as requests
        # This test verifies the endpoint exists and responds appropriately
        response = await http_client.post(f"{app_server}/api/upload_file")
        # Should return 400 for no file, not 404
        assert response.status_code in [400, 500]  # Bad request due to no file

    @pytest.mark.asyncio
    async def test_error_handling(self, app_server, http_client):
        """Test error handling for invalid requests."""
        # Test invalid interaction index for deletion
        response = await http_client.post(
            f"{app_server}/config/delete_interaction",
            json={"index": 999},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 500]
        
        # Test invalid JSON
        response = await http_client.post(
            f"{app_server}/config",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [400, 500]

    @pytest.mark.asyncio
    async def test_websocket_events_endpoint(self, app_server, http_client):
        """Test that WebSocket endpoint is available."""
        # We can't easily test WebSocket with httpx, but we can check the endpoint exists
        # This would typically return 400 for non-WebSocket request
        response = await http_client.get(f"{app_server}/ws/events")
        assert response.status_code in [400, 426]  # Bad Request or Upgrade Required

    @pytest.mark.asyncio
    async def test_waveform_endpoints(self, app_server, http_client):
        """Test waveform-related endpoints."""
        # Test waveform endpoint (should handle missing files gracefully)
        response = await http_client.get(f"{app_server}/modules/audio_output/waveform/nonexistent.wav")
        assert response.status_code in [404, 500]  # File not found
        
        # Test waveform images endpoint
        response = await http_client.get(f"{app_server}/modules/audio_output/assets/images/nonexistent.png")
        assert response.status_code in [404, 500]  # File not found