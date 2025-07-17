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
from module_loader import get_thread_pool, TaskPriority

# High-Performance Audio Processing - Integrated from performance package
import numpy as np
import pygame
from PIL import Image, ImageDraw
import os
import time
from typing import Optional, Tuple, Dict, Any
import threading
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import weakref

class OptimizedAudioProcessor:
    """
    High-performance audio processor with vectorized operations.
    
    This class provides optimized audio processing functions that replace
    inefficient loops with vectorized NumPy operations. It includes caching
    for frequently used waveforms and memory-efficient processing.
    """
    
    def __init__(self, cache_size: int = 100):
        """
        Initialize the optimized audio processor.
        
        Args:
            cache_size: Maximum number of cached waveforms
        """
        self.cache_size = cache_size
        self.waveform_cache = {}
        self.cache_lock = threading.RLock()
        self.stats = {
            "cache_hits": 0,
            "cache_misses": 0,
            "waveforms_generated": 0,
            "total_processing_time": 0.0
        }
        self.stats_lock = threading.Lock()
        
        # Thread pool for parallel processing
        self.thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="AudioProcessor")
    
    def generate_waveform_optimized(self, audio_data: np.ndarray, width: int, height: int,
                                  sample_rate: int, color: Tuple[int, int, int] = (255, 255, 255),
                                  background_color: Tuple[int, int, int] = (0, 0, 0),
                                  cache_key: Optional[str] = None) -> np.ndarray:
        """
        Generate a waveform visualization using optimized vectorized operations.
        
        Args:
            audio_data: Audio samples as numpy array
            width: Width of the waveform image
            height: Height of the waveform image
            sample_rate: Audio sample rate
            color: RGB color for the waveform
            background_color: RGB background color
            cache_key: Optional cache key for caching results
            
        Returns:
            numpy array representing the waveform image
        """
        start_time = time.time()
        
        # Check cache first
        if cache_key:
            cached_result = self._get_cached_waveform(cache_key, width, height)
            if cached_result is not None:
                with self.stats_lock:
                    self.stats["cache_hits"] += 1
                return cached_result
        
        try:
            # Convert to float32 for better performance
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Handle stereo audio by averaging channels
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Resample to fit width using vectorized operations
            if len(audio_data) > width:
                # Efficient downsampling using reshape and mean
                step = len(audio_data) // width
                remainder = len(audio_data) % width
                
                # Trim to multiple of step
                trimmed_data = audio_data[:len(audio_data) - remainder]
                
                # Reshape and take mean for efficient downsampling
                resampled = trimmed_data.reshape(-1, step).mean(axis=1)
                
                # Pad if necessary
                if len(resampled) < width:
                    resampled = np.pad(resampled, (0, width - len(resampled)), 'constant')
            else:
                # Upsample using interpolation
                resampled = np.interp(
                    np.linspace(0, len(audio_data) - 1, width),
                    np.arange(len(audio_data)),
                    audio_data
                )
            
            # Normalize to [-1, 1] range
            if np.max(np.abs(resampled)) > 0:
                resampled = resampled / np.max(np.abs(resampled))
            
            # Generate waveform using vectorized operations
            waveform_image = self._generate_waveform_vectorized(
                resampled, width, height, color, background_color
            )
            
            # Cache the result
            if cache_key:
                self._cache_waveform(cache_key, waveform_image, width, height)
            
            # Update statistics
            processing_time = time.time() - start_time
            with self.stats_lock:
                self.stats["waveforms_generated"] += 1
                self.stats["total_processing_time"] += processing_time
                if cache_key:
                    self.stats["cache_misses"] += 1
            
            return waveform_image
            
        except Exception as e:
            print(f"❌ Error in optimized waveform generation: {e}")
            # Return error pattern
            return self._generate_error_pattern(width, height, background_color)
    
    def _generate_waveform_vectorized(self, samples: np.ndarray, width: int, height: int,
                                    color: Tuple[int, int, int], 
                                    background_color: Tuple[int, int, int]) -> np.ndarray:
        """Generate waveform using vectorized operations"""
        # Create image array
        image = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        # Calculate waveform coordinates
        mid = height // 2
        amp = (height // 2) * 0.9
        
        # Vectorized coordinate calculation
        x_coords = np.arange(width)
        y_coords = (mid - samples * amp).astype(np.int32)
        
        # Clamp coordinates to image bounds
        y_coords = np.clip(y_coords, 0, height - 1)
        
        # Draw waveform using vectorized operations
        if width > 1:
            # Calculate line segments
            x1 = x_coords[:-1]
            y1 = y_coords[:-1]
            x2 = x_coords[1:]
            y2 = y_coords[1:]
            
            # Draw lines using Bresenham's algorithm (vectorized)
            for i in range(len(x1)):
                self._draw_line_optimized(image, x1[i], y1[i], x2[i], y2[i], color)
        else:
            # Single point
            if 0 <= y_coords[0] < height:
                image[y_coords[0], 0] = color
        
        return image
    
    def _draw_line_optimized(self, image: np.ndarray, x1: int, y1: int, x2: int, y2: int,
                           color: Tuple[int, int, int]):
        """Optimized line drawing using Bresenham's algorithm"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx == 0 and dy == 0:
            # Single point
            if 0 <= x1 < image.shape[1] and 0 <= y1 < image.shape[0]:
                image[y1, x1] = color
            return
        
        # Use simple interpolation for short lines
        if dx <= 1 and dy <= 1:
            for x, y in [(x1, y1), (x2, y2)]:
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    image[y, x] = color
            return
        
        # Bresenham's line algorithm
        x, y = x1, y1
        step_x = 1 if x2 > x1 else -1
        step_y = 1 if y2 > y1 else -1
        
        if dx > dy:
            error = dx / 2
            while x != x2:
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    image[y, x] = color
                error -= dy
                if error < 0:
                    y += step_y
                    error += dx
                x += step_x
        else:
            error = dy / 2
            while y != y2:
                if 0 <= x < image.shape[1] and 0 <= y < image.shape[0]:
                    image[y, x] = color
                error -= dx
                if error < 0:
                    x += step_x
                    error += dy
                y += step_y
        
        # Draw final point
        if 0 <= x2 < image.shape[1] and 0 <= y2 < image.shape[0]:
            image[y2, x2] = color
    
    def _get_cached_waveform(self, cache_key: str, width: int, height: int) -> Optional[np.ndarray]:
        """Get cached waveform if available"""
        with self.cache_lock:
            if cache_key in self.waveform_cache:
                cached_width, cached_height, waveform = self.waveform_cache[cache_key]
                if cached_width == width and cached_height == height:
                    return waveform.copy()
        return None
    
    def _cache_waveform(self, cache_key: str, waveform_data: np.ndarray, width: int, height: int):
        """Cache waveform data"""
        with self.cache_lock:
            # Implement LRU eviction if cache is full
            if len(self.waveform_cache) >= self.cache_size:
                # Remove oldest entry (simple FIFO for now)
                oldest_key = next(iter(self.waveform_cache))
                del self.waveform_cache[oldest_key]
            
            self.waveform_cache[cache_key] = (width, height, waveform_data.copy())
    
    def _generate_error_pattern(self, width: int, height: int, 
                              background_color: Tuple[int, int, int]) -> np.ndarray:
        """Generate error pattern for failed waveform generation"""
        image = np.full((height, width, 3), background_color, dtype=np.uint8)
        
        # Draw simple error pattern
        for i in range(0, min(width, height), 2):
            if i < width and i < height:
                image[i, i] = [255, 0, 0]  # Red diagonal line
        
        return image
    
    def clear_cache(self):
        """Clear the waveform cache"""
        with self.cache_lock:
            self.waveform_cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.stats_lock:
            total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
            hit_rate = (self.stats["cache_hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_size": len(self.waveform_cache),
                "cache_hit_rate": hit_rate,
                "waveforms_generated": self.stats["waveforms_generated"],
                "total_processing_time": self.stats["total_processing_time"],
                "avg_processing_time": (self.stats["total_processing_time"] / 
                                      max(self.stats["waveforms_generated"], 1))
            }
    
    def generate_pygame_waveform_optimized(self, audio_data: np.ndarray, width: int, height: int,
                                         sample_rate: int, cache_key: Optional[str] = None) -> pygame.Surface:
        """
        Generate a pygame Surface with waveform visualization using optimized operations.
        
        Args:
            audio_data: Audio samples as numpy array
            width: Width of the waveform image
            height: Height of the waveform image
            sample_rate: Audio sample rate
            cache_key: Optional cache key for caching results
            
        Returns:
            pygame.Surface with the waveform drawn
        """
        start_time = time.time()
        
        # Check cache first
        if cache_key:
            cached_result = self._get_cached_pygame_waveform(cache_key, width, height)
            if cached_result is not None:
                with self.stats_lock:
                    self.stats["cache_hits"] += 1
                return cached_result
        
        try:
            # Convert to float32 for better performance
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # Handle stereo audio by averaging channels
            if len(audio_data.shape) > 1:
                audio_data = np.mean(audio_data, axis=1)
            
            # Resample to fit width using vectorized operations
            if len(audio_data) > width:
                # Efficient downsampling using reshape and mean
                step = len(audio_data) // width
                remainder = len(audio_data) % width
                
                # Trim to multiple of step
                trimmed_data = audio_data[:len(audio_data) - remainder]
                
                # Reshape and take mean for efficient downsampling
                resampled = trimmed_data.reshape(-1, step).mean(axis=1)
                
                # Pad if necessary
                if len(resampled) < width:
                    resampled = np.pad(resampled, (0, width - len(resampled)), 'constant')
            else:
                # Upsample using interpolation
                resampled = np.interp(
                    np.linspace(0, len(audio_data) - 1, width),
                    np.arange(len(audio_data)),
                    audio_data
                )
            
            # Normalize to [-1, 1] range
            if np.max(np.abs(resampled)) > 0:
                resampled = resampled / np.max(np.abs(resampled))
            
            # Create pygame surface
            surface = pygame.Surface((width, height))
            surface.fill((0, 0, 0))  # Black background
            
            # Generate waveform using optimized drawing
            self._draw_pygame_waveform_optimized(surface, resampled, width, height)
            
            # Cache the result
            if cache_key:
                self._cache_pygame_waveform(cache_key, surface, width, height)
            
            # Update statistics
            processing_time = time.time() - start_time
            with self.stats_lock:
                self.stats["waveforms_generated"] += 1
                self.stats["total_processing_time"] += processing_time
                if cache_key:
                    self.stats["cache_misses"] += 1
            
            return surface
            
        except Exception as e:
            print(f"❌ Error in pygame waveform generation: {e}")
            # Return error pattern surface
            return self._generate_pygame_error_pattern(width, height)
    
    def _draw_pygame_waveform_optimized(self, surface: pygame.Surface, samples: np.ndarray, width: int, height: int):
        """Draw waveform on pygame surface using optimized operations"""
        # Calculate waveform coordinates
        mid = height // 2
        amp = (height // 2) * 0.9
        
        # Vectorized coordinate calculation
        x_coords = np.arange(width)
        y_coords = (mid - samples * amp).astype(np.int32)
        
        # Clamp coordinates to surface bounds
        y_coords = np.clip(y_coords, 0, height - 1)
        
        # Draw waveform using optimized line drawing
        if width > 1:
            # Calculate line segments
            x1 = x_coords[:-1]
            y1 = y_coords[:-1]
            x2 = x_coords[1:]
            y2 = y_coords[1:]
            
            # Draw lines using optimized algorithm
            for i in range(len(x1)):
                self._draw_pygame_line_optimized(surface, x1[i], y1[i], x2[i], y2[i], (255, 255, 255))
        else:
            # Single point
            if 0 <= y_coords[0] < height:
                surface.set_at((0, y_coords[0]), (255, 255, 255))
    
    def _draw_pygame_line_optimized(self, surface: pygame.Surface, x1: int, y1: int, x2: int, y2: int, color: Tuple[int, int, int]):
        """Optimized line drawing for pygame surface"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        
        if dx == 0 and dy == 0:
            # Single point
            if 0 <= x1 < surface.get_width() and 0 <= y1 < surface.get_height():
                surface.set_at((x1, y1), color)
            return
        
        # Use simple interpolation for short lines
        if dx <= 1 and dy <= 1:
            for x, y in [(x1, y1), (x2, y2)]:
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    surface.set_at((x, y), color)
            return
        
        # Bresenham's line algorithm
        x, y = x1, y1
        step_x = 1 if x2 > x1 else -1
        step_y = 1 if y2 > y1 else -1
        
        if dx > dy:
            error = dx / 2
            while x != x2:
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    surface.set_at((x, y), color)
                error -= dy
                if error < 0:
                    y += step_y
                    error += dx
                x += step_x
        else:
            error = dy / 2
            while y != y2:
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    surface.set_at((x, y), color)
                error -= dx
                if error < 0:
                    x += step_x
                    error += dy
                y += step_y
        
        # Draw final point
        if 0 <= x2 < surface.get_width() and 0 <= y2 < surface.get_height():
            surface.set_at((x2, y2), color)
    
    def _get_cached_pygame_waveform(self, cache_key: str, width: int, height: int) -> Optional[pygame.Surface]:
        """Get cached pygame waveform if available"""
        with self.cache_lock:
            if cache_key in self.waveform_cache:
                cached_width, cached_height, waveform = self.waveform_cache[cache_key]
                if cached_width == width and cached_height == height:
                    # Convert numpy array back to pygame surface
                    if isinstance(waveform, np.ndarray):
                        surface = pygame.Surface((width, height))
                        # Convert numpy array to pygame surface
                        pygame.surfarray.blit_array(surface, waveform)
                        return surface
        return None
    
    def _cache_pygame_waveform(self, cache_key: str, surface: pygame.Surface, width: int, height: int):
        """Cache pygame waveform surface"""
        with self.cache_lock:
            # Convert pygame surface to numpy array for caching
            waveform_array = pygame.surfarray.array3d(surface)
            
            # Implement LRU eviction if cache is full
            if len(self.waveform_cache) >= self.cache_size:
                # Remove oldest entry (simple FIFO for now)
                oldest_key = next(iter(self.waveform_cache))
                del self.waveform_cache[oldest_key]
            
            self.waveform_cache[cache_key] = (width, height, waveform_array)
    
    def _generate_pygame_error_pattern(self, width: int, height: int) -> pygame.Surface:
        """Generate error pattern pygame surface for failed waveform generation"""
        surface = pygame.Surface((width, height))
        surface.fill((0, 0, 0))  # Black background
        
        # Draw simple error pattern (red X)
        pygame.draw.line(surface, (255, 0, 0), (0, 0), (width, height), 3)
        pygame.draw.line(surface, (255, 0, 0), (0, height), (width, 0), 3)
        
        return surface
    
    def shutdown(self):
        """Shutdown the audio processor"""
        self.thread_pool.shutdown(wait=True)
        self.clear_cache()
        print("🛑 Optimized audio processor shutdown complete")

# Global audio processor instance
_global_audio_processor = None

def get_audio_processor() -> OptimizedAudioProcessor:
    """Get the global audio processor instance"""
    global _global_audio_processor
    if _global_audio_processor is None:
        _global_audio_processor = OptimizedAudioProcessor()
    return _global_audio_processor

def generate_waveform_optimized(audio_data: np.ndarray, width: int, height: int,
                               sample_rate: int, cache_key: Optional[str] = None) -> np.ndarray:
    """
    Convenient function to generate optimized waveform.
    
    Args:
        audio_data: Audio samples as numpy array
        width: Width of the waveform image
        height: Height of the waveform image
        sample_rate: Audio sample rate
        cache_key: Optional cache key for caching results
        
    Returns:
        numpy array representing the waveform image
    """
    return get_audio_processor().generate_waveform_optimized(
        audio_data, width, height, sample_rate, cache_key=cache_key
    )

def shutdown_audio_processor():
    """Shutdown the global audio processor"""
    global _global_audio_processor
    if _global_audio_processor:
        _global_audio_processor.shutdown()
        _global_audio_processor = None

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
    
    def __init__(self, config: Dict[str, Any], manifest: Dict[str, Any], log_callback=print, strategy=None):
        """
        Initialize the audio output module.
        
        Args:
            config (Dict[str, Any]): Module configuration
            manifest (Dict[str, Any]): Module manifest
            log_callback: Function to call for logging
            
        Note: The configuration should contain 'file_path' and 'volume' fields.
        The module will initialize pygame mixer if not already initialized.
        """
        super().__init__(config, manifest, log_callback, strategy=strategy)
        
        # Extract configuration values with defaults
        self.file_path = config.get("file_path", "")
        self.volume = config.get("volume", 100)
        # master_volume removed
        
        # Resolve relative file path to full path
        if self.file_path:
            self.file_path = self._resolve_file_path(self.file_path)
        
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
        
        broadcast_log_message(f"Audio Output initialized - File: {os.path.basename(self.file_path) if self.file_path else None}, Volume: {self.volume}%", module=self.__class__.__name__, category='audio')
        self._cursor_callback = None  # Store the GUI cursor callback

    def _resolve_file_path(self, file_path: str) -> str:
        """
        Resolve a relative file path to a full path.
        
        Args:
            file_path (str): Relative or absolute file path
            
        Returns:
            str: Full resolved file path
        """
        # If it's already an absolute path, return as is
        if os.path.isabs(file_path):
            return file_path
        
        # Try to resolve relative to the audio assets directory
        audio_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio")
        full_path = os.path.join(audio_dir, file_path)
        
        # If the file exists in the audio directory, use that path
        if os.path.exists(full_path):
            return full_path
        
        # Fallback: try relative to current working directory
        if os.path.exists(file_path):
            return os.path.abspath(file_path)
        
        # If still not found, return the original path (will be handled by error checking)
        return file_path

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
        broadcast_log_message(f"🎵 Audio output ready - {os.path.basename(self.file_path) if self.file_path else 'No file'}", module=self.__class__.__name__, category='audio')
        # Subscribe to module_event events with a filter for matching input settings
        def event_filter(event, settings):
            # Match on settings if needed (e.g., input port/address, etc.)
            # For now, accept all events; refine as needed for your routing logic
            return True
        # EventRouter is no longer used; replaced by performance package
    
    def stop(self):
        """
        Stop the audio output module and clean up resources.
        This method stops any currently playing audio and cleans up
        pygame mixer resources if this is the last audio module.
        Note: pygame mixer is shared across all audio modules, so it's only
        stopped when all audio modules are stopped.
        """
        # Stop current playback
        if self.current_channel and self.current_channel.get_busy():
            self.current_channel.stop()
            self.current_channel = None
        # Clean up any additional resources here (threads, files, etc.)
        # (If you add threads or open files in the future, stop/close them here.)
        super().stop()
        broadcast_log_message(f"🛑 Audio output stopped (instance {self.instance_id})", module=self.__class__.__name__, category='audio')

    def wait_for_stop(self):
        """
        Wait for any background tasks/threads to finish (future-proof).
        """
        # No background threads currently, but method is here for consistency
        pass
    
    def handle_event(self, event, settings=None):
        """
        Handle incoming events by playing audio.
        This method is called when the module receives an event from a connected input module.
        """
        if self.strategy:
            self.strategy.process_event(event)
        else:
            data = event['data'] if isinstance(event, dict) and 'data' in event else event
            if getattr(self, 'log_level', 'info') == 'verbose':
                broadcast_log_message(f"🎵 Current file_path: {self.file_path}", module=self.__class__.__name__, category='audio')
                broadcast_log_message(f"🎵 Current volume: {self.volume}", module=self.__class__.__name__, category='audio')
            if not self.file_path or not os.path.exists(self.file_path):
                broadcast_log_message("❌ No audio file configured or file not found", module=self.__class__.__name__, category='audio')
                return
            try:
                import pygame
                sound = pygame.mixer.Sound(self.file_path)
                final_volume = self.volume / 100.0
                broadcast_log_message(f"🎵 Setting volume: {final_volume} (individual: {self.volume})", module=self.__class__.__name__, category='audio')
                sound.set_volume(final_volume)
                channel = pygame.mixer.find_channel()
                if channel:
                    channel.play(sound)
                    self.current_channel = channel
                    self.playback_start_time = time.time()
                    self.audio_duration = sound.get_length()
                    filename = os.path.basename(self.file_path)
                    broadcast_log_message(f"Audio Clip: {filename} played", module=self.__class__.__name__, category='audio')
                    if self._cursor_callback:
                        self._cursor_callback(self.audio_duration)
            except Exception as e:
                broadcast_log_message(f"❌ Error playing audio: {e}", module=self.__class__.__name__, category='audio')
    
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
        
        # Resolve relative file path to full path
        if self.file_path:
            self.file_path = self._resolve_file_path(self.file_path)
        
        # Handle file path changes
        if old_file_path != self.file_path:
            broadcast_log_message(f"🔄 Audio file changed to: {os.path.basename(self.file_path) if self.file_path else 'None'}", module=self.__class__.__name__, category='audio')
            
            # Generate new waveform if file exists
            if self.file_path and os.path.exists(self.file_path):
                self.generate_waveform()
            else:
                self.waveform_data = None
                self.waveform_image_path = None
        
        # Handle volume changes
        if old_volume != self.volume:
            broadcast_log_message(f"🔊 Volume changed to: {self.volume}%", module=self.__class__.__name__, category='audio')
    
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
                    framerate = wf.getframerate()
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
                # Optimized waveform generation
                processor = get_audio_processor()
                surface = processor.generate_pygame_waveform_optimized(samples, width, height, framerate, cache_key=file_path)
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
                AudioOutputModule.generate_waveform_static(self.file_path, self.waveform_image_path, log_callback=broadcast_log_message)
                
                broadcast_log_message(f"📊 Generated waveform for {filename}", module=self.__class__.__name__, category='audio')
            else:
                broadcast_log_message(f"📊 Using cached waveform for {filename}", module=self.__class__.__name__, category='audio')
                
        except Exception as e:
            broadcast_log_message(f"❌ Error generating waveform: {e}", module=self.__class__.__name__, category='audio')
    
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
            broadcast_log_message(f"❌ Matplotlib waveform generation failed: {e}", module=self.__class__.__name__, category='audio')
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
                # Optimized waveform generation
                processor = get_audio_processor()
                surface = processor.generate_pygame_waveform_optimized(samples, width, height, framerate, cache_key=self.file_path)
                broadcast_log_message(f"📊 Generated waveform (pygame) for {os.path.basename(self.file_path)}", module=self.__class__.__name__, category='audio')
            except Exception as e:
                # Draw a red X if file is not a valid WAV
                pygame.draw.line(surface, (255, 0, 0), (0, 0), (width, height), 3)
                pygame.draw.line(surface, (255, 0, 0), (0, height), (width, 0), 3)
                broadcast_log_message(f"❌ Pygame waveform generation failed: {e}", module=self.__class__.__name__, category='audio')
            # Save the surface
            if self.waveform_image_path:
                pygame.image.save(surface, self.waveform_image_path)
        except Exception as e:
            broadcast_log_message(f"❌ Pygame waveform generation outer error: {e}", module=self.__class__.__name__, category='audio')
    
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
                broadcast_log_message(f"[Auto-configure] Selected file: {self.file_path}", module=self.__class__.__name__, category='audio')
        if not getattr(self, 'volume', None):
            self.volume = 100
            self.config['volume'] = 100
            broadcast_log_message("[Auto-configure] Set default volume: 100", module=self.__class__.__name__, category='audio')

