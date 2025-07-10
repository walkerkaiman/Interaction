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
        # master_volume removed
        
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
        self._cursor_callback = None  # Store the GUI cursor callback
    
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
        # Clean up any additional resources here (threads, files, etc.)
        # (If you add threads or open files in the future, stop/close them here.)
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
        if getattr(self, 'log_level', 'info') == 'verbose':
            self.log_message(f"🎵 Audio output received event: {data}")
        if getattr(self, 'log_level', 'info') == 'verbose':
            self.log_message(f"🎵 Current file_path: {self.file_path}")
        if getattr(self, 'log_level', 'info') == 'verbose':
            self.log_message(f"🎵 Current volume: {self.volume}")
        
        if not self.file_path or not os.path.exists(self.file_path):
            self.log_message("❌ No audio file configured or file not found")
            return
        
        try:
            # Load the audio file
            if getattr(self, 'log_level', 'info') == 'verbose':
                self.log_message(f"🎵 Loading audio file: {self.file_path}")
            sound = pygame.mixer.Sound(self.file_path)
            
            # Calculate final volume (individual * master)
            final_volume = self.volume / 100.0
            self.log_message(f"🎵 Setting volume: {final_volume} (individual: {self.volume})")
            self.log_message(f"🎵 Volume calculation: {self.volume} / 100.0 = {final_volume}")
            sound.set_volume(final_volume)
            
            # Play the audio on an available channel
            channel = pygame.mixer.find_channel()
            if channel:
                if getattr(self, 'log_level', 'info') == 'verbose':
                    self.log_message(f"🎵 Playing audio on channel")
                channel.play(sound)
                self.current_channel = channel
                self.playback_start_time = time.time()
                
                # Get audio duration for cursor tracking
                self.audio_duration = sound.get_length()
                if getattr(self, 'log_level', 'info') == 'verbose':
                    self.log_message(f"🎵 Audio duration: {self.audio_duration} seconds")
                
                # Log the playback
                filename = os.path.basename(self.file_path)
                self.log_message(f"🎵 Playing {filename}")
                
                # Start cursor animation if GUI callback is available
                if self._cursor_callback:
                    if getattr(self, 'log_level', 'info') == 'verbose':
                        self.log_message(f"🎵 Starting cursor animation")
                    self._cursor_callback(self.audio_duration)
                else:
                    if getattr(self, 'log_level', 'info') == 'verbose':
                        self.log_message(f"⚠️ No cursor callback available")
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
    
    # set_master_volume removed
    
    @staticmethod
    def generate_waveform_static(file_path, output_path, log_callback=print):
        """
        Static method to generate a waveform image from a WAV file.
        Used for GUI preview/generation without instantiating the module.
        """
        import os
        import numpy as np
        import wave
        import pygame
        try:
            # Try matplotlib first
            try:
                import matplotlib
                matplotlib.use('Agg')
                import matplotlib.pyplot as plt
                from pydub import AudioSegment
                audio = AudioSegment.from_wav(file_path)
                samples = np.array(audio.get_array_of_samples())
                if len(samples) > 10000:
                    step = len(samples) // 10000
                    samples = samples[::step]
                plt.figure(figsize=(8, 2))
                plt.plot(samples, color='white', linewidth=0.5)
                plt.axis('off')
                plt.gca().set_facecolor('black')
                plt.gcf().set_facecolor('black')
                plt.savefig(output_path, bbox_inches='tight', pad_inches=0, facecolor='black', edgecolor='none')
                plt.close()
                log_callback(f"📊 [static] Generated waveform (matplotlib) for {os.path.basename(file_path)}")
                return True
            except Exception as e:
                log_callback(f"❌ [static] Matplotlib waveform generation failed: {e}")
            # Fallback to pygame
            width, height = 800, 200
            surface = pygame.Surface((width, height))
            surface.fill((0, 0, 0))
            try:
                with wave.open(file_path, 'rb') as wf:
                    n_channels = wf.getnchannels()
                    n_frames = wf.getnframes()
                    sampwidth = wf.getsampwidth()
                    frames = wf.readframes(n_frames)
                dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(sampwidth, np.int16)
                samples = np.frombuffer(frames, dtype=dtype)
                if n_channels > 1:
                    samples = samples[::n_channels]
                if len(samples) > width:
                    step = len(samples) // width
                    samples = samples[::step][:width]
                else:
                    samples = np.pad(samples, (0, width - len(samples)), 'constant')
                samples = samples.astype(np.float32)
                if np.max(np.abs(samples)) > 0:
                    samples /= np.max(np.abs(samples))
                mid = height // 2
                amp = (height // 2) * 0.9
                points = [(x, int(mid - s * amp)) for x, s in enumerate(samples)]
                for x in range(1, len(points)):
                    pygame.draw.line(surface, (255, 255, 255), points[x-1], points[x], 1)
                log_callback(f"📊 [static] Generated waveform (pygame) for {os.path.basename(file_path)}")
            except Exception as e:
                pygame.draw.line(surface, (255, 0, 0), (0, 0), (width, height), 3)
                pygame.draw.line(surface, (255, 0, 0), (0, height), (width, 0), 3)
                log_callback(f"❌ [static] Pygame waveform generation failed: {e}")
            pygame.image.save(surface, output_path)
            return True
        except Exception as e:
            log_callback(f"❌ [static] Waveform generation outer error: {e}")
            return False

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
            module_dir = os.path.dirname(os.path.abspath(__file__))
            waveform_dir = os.path.join(module_dir, "waveform")
            os.makedirs(waveform_dir, exist_ok=True)
            
            filename = os.path.basename(self.file_path)
            waveform_filename = f"{filename}.waveform.png"
            self.waveform_image_path = os.path.join(waveform_dir, waveform_filename)
            
            # Generate waveform if it doesn't exist
            if not os.path.exists(self.waveform_image_path):
                AudioOutputModule.generate_waveform_static(self.file_path, self.waveform_image_path, log_callback=self.log_message)
                
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
        This method uses pygame to create a waveform visualization from the actual audio data.
        If the file is not a valid WAV, it draws a red X and logs an error.
        """
        import wave
        try:
            width, height = 800, 200
            surface = pygame.Surface((width, height))
            surface.fill((0, 0, 0))  # Black background
            # Try to read the WAV file
            try:
                with wave.open(self.file_path, 'rb') as wf:
                    n_channels = wf.getnchannels()
                    n_frames = wf.getnframes()
                    sampwidth = wf.getsampwidth()
                    framerate = wf.getframerate()
                    frames = wf.readframes(n_frames)
                # Convert to numpy array
                import numpy as np
                dtype = {1: np.int8, 2: np.int16, 4: np.int32}.get(sampwidth, np.int16)
                samples = np.frombuffer(frames, dtype=dtype)
                if n_channels > 1:
                    samples = samples[::n_channels]  # Use first channel
                # Downsample for visualization
                if len(samples) > width:
                    step = len(samples) // width
                    samples = samples[::step][:width]
                else:
                    samples = np.pad(samples, (0, width - len(samples)), 'constant')
                # Normalize to -1..1
                samples = samples.astype(np.float32)
                if np.max(np.abs(samples)) > 0:
                    samples /= np.max(np.abs(samples))
                # Draw waveform
                mid = height // 2
                amp = (height // 2) * 0.9
                points = [(x, int(mid - s * amp)) for x, s in enumerate(samples)]
                for x in range(1, len(points)):
                    pygame.draw.line(surface, (255, 255, 255), points[x-1], points[x], 1)
                self.log_message(f"📊 Generated waveform (pygame) for {os.path.basename(self.file_path)}")
            except Exception as e:
                # Draw a red X if file is not a valid WAV
                pygame.draw.line(surface, (255, 0, 0), (0, 0), (width, height), 3)
                pygame.draw.line(surface, (255, 0, 0), (0, height), (width, 0), 3)
                self.log_message(f"❌ Pygame waveform generation failed: {e}")
            # Save the surface
            if self.waveform_image_path:
                pygame.image.save(surface, self.waveform_image_path)
        except Exception as e:
            self.log_message(f"❌ Pygame waveform generation outer error: {e}")
    
    def get_waveform_path(self) -> Optional[str]:
        """
        Get the path to the waveform image file.
        
        Returns:
            Optional[str]: Path to waveform image, or None if not available
            
        Note: This method is used by the GUI to display the waveform
        visualization for the audio file.
        """
        # Always recalculate the expected path based on the new scheme
        if not self.file_path:
            return None
        module_dir = os.path.dirname(os.path.abspath(__file__))
        waveform_dir = os.path.join(module_dir, "waveform")
        filename = os.path.basename(self.file_path)
        waveform_filename = f"{filename}.waveform.png"
        path = os.path.join(waveform_dir, waveform_filename)
        return path if os.path.exists(path) else None
    
    def get_waveform_image_path(self) -> Optional[str]:
        """
        Alias for get_waveform_path, for GUI compatibility.
        """
        return self.get_waveform_path()
    
    def get_waveform_label(self) -> str:
        """
        Return the label to display above the waveform: the filename if loaded, otherwise 'Playback'.
        """
        if self.file_path:
            return os.path.basename(self.file_path)
        return "Playback"
    
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

    def set_cursor_callback(self, callback):
        """
        Set a callback to be called with the audio duration when playback starts (for GUI cursor animation).
        """
        self._cursor_callback = callback

    def get_field_label(self, field_name):
        """Return the display label for a given field."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('label', field_name)
        return field_name

    def get_field_type(self, field_name):
        """Return the type for a given field (e.g., 'slider', 'text')."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('type', 'text')
        return 'text'

    def get_field_default(self, field_name):
        """Return the default value for a given field."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('default', '')
        return ''

    def get_field_options(self, field_name):
        """Return options for a given field (for dropdowns, etc.), or None."""
        if hasattr(self, 'manifest') and 'fields' in self.manifest:
            for field in self.manifest['fields']:
                if field['name'] == field_name:
                    return field.get('options')
        return None

    def auto_configure(self):
        """
        If no file_path is set, select the first .wav file in the module directory. Set volume to 100 if not set.
        """
        import os
        if not getattr(self, 'file_path', None):
            module_dir = os.path.dirname(__file__)
            wavs = [f for f in os.listdir(module_dir) if f.lower().endswith('.wav')]
            if wavs:
                self.file_path = os.path.join(module_dir, wavs[0])
                self.config['file_path'] = self.file_path
                self.log_message(f"[Auto-configure] Selected file: {self.file_path}")
        if not getattr(self, 'volume', None):
            self.volume = 100
            self.config['volume'] = 100
            self.log_message("[Auto-configure] Set default volume: 100")

