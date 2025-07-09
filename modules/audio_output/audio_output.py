from modules.module_base import ModuleBase
from threading import Thread
from time import sleep
import os
import numpy as np
import pygame
import pygame.mixer


class AudioOutput(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.play_thread = None
        self.playing = False
        # Load volume from config (stored as percentage, convert to 0.0-1.0)
        volume_from_config = float(self.config.get("volume", 100.0))
        self.volume = round(volume_from_config / 100.0, 3)  # Convert percentage to 0.0-1.0, rounded
        self.master_volume = 1.0  # Master volume from GUI (0.0 to 1.0)
        self.cursor_position = 0.0  # 0.0 to 1.0 for waveform cursor
        self.cursor_callback = None  # Callback for cursor updates
        self.current_process = None  # Store current audio process
        
        # Initialize waveform
        self.waveform_image_path = None
        
        # Auto-load existing waveform or generate new one on startup
        file_path = self.config.get("file_path", "")
        if file_path:
            self.log_message(f"🔄 Auto-loading waveform on startup for: {file_path}", level="verbose")
            self.generate_waveform(file_path)

    def start(self):
        self.log_message("Audio output module ready.", level="verbose")

    def stop(self):
        if self.playing:
            # Stop all pygame mixer channels
            pygame.mixer.stop()
            self.playing = False
            self.cursor_position = 0.0
            if self.cursor_callback:
                self.cursor_callback(0.0)
        self.log_message("Audio output stopped.", level="show_mode")

    def set_cursor_callback(self, callback):
        """Set callback for cursor position updates"""
        self.cursor_callback = callback
        self.log_message(f"🎵 Cursor callback set: {callback is not None}", level="verbose")

    def handle_event(self, data=None):
        self.log_message(f"📨 handle_event() triggered with data: {data}", level="output_trigger")
        file_path = self.config.get("file_path", "")
        self.log_message(f"📁 file_path from config: {file_path}", level="verbose")
        if not file_path or not os.path.isfile(file_path):
            self.log_message("⚠️ No valid audio file configured.", level="show_mode")
            return

        # Start new playback thread (non-blocking)
        self.play_thread = Thread(target=self._play_audio, args=(file_path,))
        self.play_thread.daemon = True
        self.play_thread.start()

    def _play_audio(self, file_path):
        """Play audio using pygame mixer for concurrent playback"""
        try:
            self.playing = True
            
            # Initialize pygame mixer if not already done
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
            
            # Load and play the sound
            sound = pygame.mixer.Sound(file_path)
            
            # Apply volume
            effective_volume = self.get_effective_volume()
            sound.set_volume(effective_volume)
            
            # Find an available channel
            channel = pygame.mixer.find_channel()
            if channel is None:
                # If no channel available, use channel 0
                channel = pygame.mixer.Channel(0)
            
            # Play the sound
            channel.play(sound)
            
            self.log_message(f"▶️ Playing: {os.path.basename(file_path)} (volume: {int(effective_volume * 100)}%)", level="output_trigger")
            
            # Get duration for cursor tracking
            duration = sound.get_length()
            
            # Start cursor tracking using the new system - only when audio actually starts
            if self.cursor_callback:
                self.log_message(f"🎵 Starting cursor animation for {duration:.2f}s audio", level="verbose")
                # Call the new cursor system with duration
                self.cursor_callback(duration)
            else:
                self.log_message(f"⚠️ No cursor callback set", level="verbose")
            
            # Wait for playback to complete
            while channel.get_busy():
                sleep(0.1)
            
            # Reset cursor when done
            if self.cursor_callback:
                self.cursor_callback(0.0)
            
        except Exception as e:
            self.log_message(f"⚠️ Playback error: {e}", level="show_mode")
            self.playing = False
            self.cursor_position = 0.0
            if self.cursor_callback:
                self.cursor_callback(0.0)

    def _estimate_duration(self, file_path):
        """Estimate audio duration for cursor tracking"""
        try:
            # Use pygame to get duration
            sound = pygame.mixer.Sound(file_path)
            return sound.get_length()
        except Exception:
            # Fallback: estimate based on file size and typical bitrate
            file_size = os.path.getsize(file_path)
            # Assume 16-bit, 44.1kHz, stereo WAV (rough estimate)
            estimated_duration = file_size / (44100 * 2 * 2)  # bytes / (sample_rate * channels * bytes_per_sample)
            return max(1.0, estimated_duration)  # Minimum 1 second

    def _track_cursor(self, duration, channel):
        """Track cursor position during playback"""
        steps = 100  # Cursor resolution
        delay = duration / steps

        for i in range(steps + 1):  # Include step 0 and 100
            if not self.playing or not channel.get_busy():
                break
            self.cursor_position = i / steps  # This gives 0.0 to 1.0
            if self.cursor_callback:
                self.cursor_callback(self.cursor_position)
            sleep(delay)

        # Reset cursor when done
        self.cursor_position = 0.0
        self.playing = False
        if self.cursor_callback:
            self.cursor_callback(0.0)

    def set_volume(self, volume):
        """Set individual volume (0.0 to 1.0)"""
        self.volume = round(max(0.0, min(1.0, volume)), 3)
        # Save as percentage in config, rounded to avoid precision issues
        self.config["volume"] = round(self.volume * 100.0, 1)
        self.log_message(f"🔊 Individual volume set to: {int(self.volume * 100)}%", level="verbose")

    def set_master_volume(self, volume):
        """Set master volume (0.0 to 1.0)"""
        self.master_volume = round(max(0.0, min(1.0, volume)), 3)
        self.log_message(f"🔊 Master volume set to: {int(self.master_volume * 100)}%", level="verbose")

    def get_volume(self):
        """Get current volume"""
        return self.volume

    def get_effective_volume(self):
        """Get effective volume (individual * master)"""
        effective = round(self.volume * self.master_volume, 3)
        # Debug logging
        self.log_message(f"🔊 Volume debug - Individual: {self.volume:.2f}, Master: {self.master_volume:.2f}, Effective: {effective:.2f}", level="verbose")
        return effective

    def get_cursor_position(self):
        """Get current cursor position (0.0 to 1.0)"""
        return self.cursor_position

    def generate_waveform(self, audio_file_path):
        """Generate waveform visualization for audio file"""
        if not audio_file_path or not os.path.exists(audio_file_path):
            self.log_message(f"⚠️ No valid audio file for waveform: {audio_file_path}", level="show_mode")
            return None
            
        try:
            waveform_path = f"{audio_file_path}.waveform.png"
            
            # Check if waveform already exists
            if os.path.exists(waveform_path):
                self.waveform_image_path = waveform_path
                self.log_message(f"📈 Using existing waveform: {waveform_path}", level="verbose")
                return waveform_path
            
            self.log_message(f"🔄 Generating waveform for: {audio_file_path}", level="verbose")
            
            # Try pydub first (better quality)
            try:
                from pydub import AudioSegment
                from pydub.utils import make_chunks
                
                audio = AudioSegment.from_file(audio_file_path)
                samples = []
                chunk_length_ms = 10  # 10ms chunks
                chunks = make_chunks(audio, chunk_length_ms)
                
                for chunk in chunks:
                    # Get RMS (root mean square) for volume
                    samples.append(chunk.rms)
                
                self.log_message(f"📊 Audio loaded with pydub: {len(samples)} samples, duration: {len(audio)/1000:.2f}s", level="verbose")
                
            except ImportError as e:
                self.log_message(f"⚠️ pydub failed due to missing pyaudioop, trying wave fallback...", level="show_mode")
                # Fallback to wave module
                try:
                    import wave
                    with wave.open(audio_file_path, 'rb') as wav_file:
                        # Get audio data
                        frames = wav_file.readframes(wav_file.getnframes())
                        # Convert to numpy array
                        import struct
                        if wav_file.getsampwidth() == 2:  # 16-bit
                            samples = struct.unpack(f'<{len(frames)//2}h', frames)
                        else:  # 8-bit
                            samples = struct.unpack(f'<{len(frames)}B', frames)
                        
                        # Convert to list and downsample
                        samples = list(samples)
                        step = max(1, len(samples) // 1000)
                        samples = samples[::step]
                        
                        self.log_message(f"📊 Audio loaded with wave fallback: {len(samples)} samples", level="verbose")
                        
                except Exception as wave_error:
                    self.log_message(f"⚠️ wave fallback also failed: {wave_error}", level="show_mode")
                    return None
            
            # Create waveform visualization
            import matplotlib
            matplotlib.use('Agg')  # Use non-interactive backend to avoid GUI conflicts
            import matplotlib.pyplot as plt
            
            try:
                plt.figure(figsize=(8, 2))
                plt.plot(samples, color='black', linewidth=0.5)
                plt.axis('off')
                plt.tight_layout()
                plt.savefig(waveform_path, bbox_inches='tight', pad_inches=0, dpi=100)
                plt.close()

                self.waveform_image_path = waveform_path
                self.log_message(f"✅ Waveform generated: {waveform_path}", level="verbose")
                return waveform_path
                
            except Exception as plot_error:
                self.log_message(f"⚠️ Failed to create plot: {plot_error}", level="show_mode")
                return None
                
        except Exception as e:
            self.log_message(f"⚠️ Waveform generation failed: {e}", level="show_mode")
            return None
    
    def get_waveform_image_path(self):
        path = getattr(self, "waveform_image_path", None)
        if path:
            self.log_message(f"🔍 Waveform path: {path} (exists: {os.path.exists(path)})", level="verbose")
        else:
            self.log_message("🔍 No waveform path available", level="verbose")
        return path

