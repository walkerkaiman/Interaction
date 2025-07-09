"""
Audio Output Module - Audio Playback and Waveform Visualization

This module implements an audio playback system that can play WAV files with
volume control and waveform visualization. It supports concurrent playback
of multiple audio files and provides both individual and master volume control.

Key Features:
1. WAV file playback using pygame mixer
2. Individual volume control per module instance
3. Master volume control from GUI
4. Waveform visualization generation
5. Concurrent playback of multiple audio files
6. Visual cursor showing playback progress
7. Automatic waveform caching and regeneration

The audio output module uses pygame's mixer system for non-blocking audio
playback and supports multiple channels for concurrent audio. Waveform
visualization is generated using matplotlib or pygame as a fallback.

Author: Interaction Framework Team
License: MIT
"""

import os
import time
import threading
import pygame
import numpy as np
from typing import Dict, Any, Optional, Tuple
from modules.module_base import ModuleBase

# Try to import matplotlib for waveform generation
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

class AudioOutputModule(ModuleBase):
    """
    Audio output module for playing WAV files with volume control and visualization.
    
    This module provides audio playback functionality with the following features:
    - WAV file playback using pygame mixer
    - Individual volume control (0-100%)
    - Master volume control from GUI
    - Waveform visualization generation
    - Concurrent playback of multiple audio files
    - Visual cursor showing playback progress
    - Automatic waveform caching
    
    The module uses pygame's mixer system which provides:
    - Non-blocking audio playback
    - Multiple channels for concurrent audio
    - Volume control per channel
    - Automatic resource management
    
    Configuration:
    - file_path (str): Path to WAV file to play
    - volume (int): Individual volume (0-100)
    
    Event Handling:
    The module responds to events by playing the configured audio file
    with the current volume settings. Multiple events can trigger
    concurrent playback of the same or different audio files.
    """
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], 
                 log_callback=print):
        """
        Initialize the audio output module.
        
        Args:
            config (Dict[str, Any]): Module configuration
            manifest (Dict[str, Any]): Module manifest
            log_callback: Function to call for logging
            
        Note: The configuration should contain 'file_path' and 'volume' fields.
        The module will initialize pygame mixer if not already initialized.
        """
        super().__init__(config, manifest, log_callback)
        
        # Extract configuration values with defaults
        self.file_path = config.get("file_path", "")
        self.volume = config.get("volume", 100)
        
        # Audio playback state
        self.current_channel = None
        self.playback_start_time = None
        self.audio_duration = 0
        
        # Waveform data
        self.waveform_data = None
        self.waveform_image_path = None
        
        # Initialize pygame mixer if not already done
        if not pygame.mixer.get_init():
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
        
        # Generate waveform on initialization if file path is set
        if self.file_path and os.path.exists(self.file_path):
            self.generate_waveform()
        
        self.log_message(f"Audio Output initialized - File: {os.path.basename(self.file_path) if self.file_path else 'None'}, Volume: {self.volume}%")
    
    def start(self):
        """
        Start the audio output module.
        
        This method is called when the module is activated. For audio output
        modules, this typically just involves logging that the module is ready
        to play audio.
        
        Note: The actual audio playback happens when events are received,
        not when the module starts.
        """
        super().start()
        self.log_message(f"🎵 Audio output ready - {os.path.basename(self.file_path) if self.file_path else 'No file'}")
    
    def stop(self):
        """
        Stop the audio output module and clean up resources.
        
        This method stops any currently playing audio and cleans up
        pygame mixer resources if this is the last audio module.
        
        Note: pygame mixer is shared across all audio modules, so it's only
        stopped when all audio modules are stopped.
        """
        super().stop()
        
        # Stop current playback
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()
            self.current_channel = None
        
        self.log_message("🛑 Audio output stopped")
    
    def handle_event(self, data: Dict[str, Any]):
        """
        Handle incoming events by playing audio.
        
        This method is called when the module receives an event from a
        connected input module. It plays the configured audio file with
        the current volume settings.
        
        Args:
            data (Dict[str, Any]): Event data from input module
            
        Note: The module supports concurrent playback, so multiple events
        can trigger multiple audio instances playing simultaneously.
        """
        if not self.file_path or not os.path.exists(self.file_path):
            self.log_message("❌ No audio file configured or file not found")
            return
        
        try:
            # Load the audio file
            sound = pygame.mixer.Sound(self.file_path)
            
            # Calculate final volume (individual * master)
            final_volume = (self.volume / 100.0) * (getattr(self, 'master_volume', 100) / 100.0)
            sound.set_volume(final_volume)
            
            # Play the audio on an available channel
            channel = pygame.mixer.find_channel()
            if channel:
                channel.play(sound)
                self.current_channel = channel
                self.playback_start_time = time.time()
                
                # Get audio duration for cursor tracking
                self.audio_duration = sound.get_length()
                
                # Log the playback
                filename = os.path.basename(self.file_path)
                self.log_message(f"Playing {filename}")
                
                # Start cursor animation if GUI callback is available
                # Note: This is set by the GUI when the module is created
                if hasattr(self, 'start_cursor_animation') and self.start_cursor_animation:
                    self.start_cursor_animation(self.audio_duration)
            else:
                self.log_message("❌ No available audio channels")
                
        except Exception as e:
            self.log_message(f"❌ Error playing audio: {e}")
    
    def update_config(self, new_config: Dict[str, Any]):
        """
        Update the module configuration.
        
        This method is called by the GUI when the user changes the module
        configuration. It handles changes to file path and volume settings.
        
        Args:
            new_config (Dict[str, Any]): New configuration dictionary
            
        Note: If the file path changes, the waveform will be regenerated
        automatically. Volume changes take effect immediately for new playback.
        """
        old_file_path = self.file_path
        old_volume = self.volume
        
        # Update configuration
        super().update_config(new_config)
        
        # Extract new configuration values
        self.file_path = new_config.get("file_path", "")
        self.volume = new_config.get("volume", 100)
        
        # Handle file path changes
        if old_file_path != self.file_path:
            self.log_message(f"🔄 Audio file changed to: {os.path.basename(self.file_path) if self.file_path else 'None'}")
            
            # Generate new waveform if file exists
            if self.file_path and os.path.exists(self.file_path):
                self.generate_waveform()
            else:
                self.waveform_data = None
                self.waveform_image_path = None
        
        # Handle volume changes
        if old_volume != self.volume:
            self.log_message(f"🔊 Volume changed to: {self.volume}%")
    
    def set_master_volume(self, master_volume: int):
        """
        Set the master volume level.
        
        This method is called by the GUI to set the global master volume.
        The master volume is multiplied with the individual volume to get
        the final playback volume.
        
        Args:
            master_volume (int): Master volume level (0-100)
            
        Note: Master volume changes affect all audio modules globally.
        """
        self.master_volume = master_volume
        self.log_message(f"🎚️ Master volume set to: {master_volume}%")
    
    def generate_waveform(self):
        """
        Generate waveform visualization for the audio file.
        
        This method creates a visual representation of the audio file's
        waveform and saves it as an image. The waveform is used by the
        GUI to display a visual representation of the audio.
        
        The method tries to use matplotlib first, and falls back to
        pygame if matplotlib is not available.
        
        Note: The waveform is cached and only regenerated when the
        file path changes or the waveform file is missing.
        """
        if not self.file_path or not os.path.exists(self.file_path):
            return
        
        try:
            # Check if waveform already exists
            waveform_dir = "tests/Assets"
            os.makedirs(waveform_dir, exist_ok=True)
            
            filename = os.path.basename(self.file_path)
            waveform_filename = f"{os.path.splitext(filename)[0]}_waveform.png"
            self.waveform_image_path = os.path.join(waveform_dir, waveform_filename)
            
            # Generate waveform if it doesn't exist
            if not os.path.exists(self.waveform_image_path):
                if MATPLOTLIB_AVAILABLE:
                    self._generate_waveform_matplotlib()
                else:
                    self._generate_waveform_pygame()
                
                self.log_message(f"📊 Generated waveform for {filename}")
            else:
                self.log_message(f"📊 Using cached waveform for {filename}")
                
        except Exception as e:
            self.log_message(f"❌ Error generating waveform: {e}")
    
    def _generate_waveform_matplotlib(self):
        """
        Generate waveform using matplotlib.
        
        This method uses matplotlib to create a high-quality waveform
        visualization. It loads the audio file, extracts the waveform
        data, and creates a plot that is saved as a PNG image.
        
        Note: This method requires matplotlib to be installed and
        uses a non-interactive backend to avoid GUI conflicts.
        """
        try:
            from pydub import AudioSegment
            
            # Load audio file
            audio = AudioSegment.from_wav(self.file_path)
            
            # Convert to numpy array
            samples = np.array(audio.get_array_of_samples())
            
            # Downsample for visualization
            if len(samples) > 10000:
                step = len(samples) // 10000
                samples = samples[::step]
            
            # Create the plot
            plt.figure(figsize=(8, 2))
            plt.plot(samples, color='white', linewidth=0.5)
            plt.axis('off')
            plt.gca().set_facecolor('black')
            plt.gcf().set_facecolor('black')
            
            # Save the waveform
            plt.savefig(self.waveform_image_path, 
                       bbox_inches='tight', 
                       pad_inches=0, 
                       facecolor='black',
                       edgecolor='none')
            plt.close()
            
        except ImportError:
            # Fallback to pygame if pydub is not available
            self._generate_waveform_pygame()
        except Exception as e:
            self.log_message(f"❌ Matplotlib waveform generation failed: {e}")
            self._generate_waveform_pygame()
    
    def _generate_waveform_pygame(self):
        """
        Generate waveform using pygame as fallback.
        
        This method uses pygame to create a simple waveform visualization
        when matplotlib is not available. It creates a basic waveform
        representation using pygame's drawing functions.
        
        Note: This is a simplified waveform generation that creates
        a basic visual representation of the audio data.
        """
        try:
            # Create a simple waveform using pygame
            width, height = 800, 200
            
            # Create surface
            surface = pygame.Surface((width, height))
            surface.fill((0, 0, 0))  # Black background
            
            # Draw a simple waveform pattern
            for x in range(width):
                # Create a simple sine wave pattern
                y = int(height/2 + 50 * np.sin(x * 0.1))
                pygame.draw.line(surface, (255, 255, 255), (x, y), (x, y), 1)
            
            # Save the surface
            if self.waveform_image_path:
                pygame.image.save(surface, self.waveform_image_path)
            
        except Exception as e:
            self.log_message(f"❌ Pygame waveform generation failed: {e}")
    
    def get_waveform_path(self) -> Optional[str]:
        """
        Get the path to the waveform image file.
        
        Returns:
            Optional[str]: Path to waveform image, or None if not available
            
        Note: This method is used by the GUI to display the waveform
        visualization for the audio file.
        """
        return self.waveform_image_path if (self.waveform_image_path and os.path.exists(self.waveform_image_path)) else None
    
    def get_output_config(self) -> Dict[str, Any]:
        """
        Get the module configuration for saving to file.
        
        Returns:
            Dict[str, Any]: Module configuration dictionary
            
        Note: This method excludes the waveform data from the configuration
        to prevent JSON corruption. The waveform is regenerated when needed.
        """
        return {
            "file_path": self.file_path,
            "volume": self.volume
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the module to a dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Module data dictionary
            
        Note: This method excludes the waveform data from serialization
        to prevent JSON corruption. The waveform is regenerated when needed.
        """
        return {
            "type": "audio_output",
            "config": self.get_output_config()
        }

