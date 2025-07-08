from modules.module_base import BaseModule
from pygame import mixer
from threading import Thread
from time import sleep
import os
import numpy as np


class AudioOutput(BaseModule):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.play_thread = None
        self.playing = False
        self.waveform_image_path = None
        mixer.init()

    def start(self):
        self.log_message("Audio output module ready.")
        self._maybe_generate_waveform()

    def stop(self):
        if self.playing:
            mixer.music.stop()
        self.log_message("Audio output stopped.")

    def handle_event(self, data=None):
        file_path = self.config.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            self.log_message("⚠️ No valid audio file configured.")
            return

        if self.playing:
            mixer.music.stop()

        try:
            mixer.music.load(file_path)
            duration = mixer.Sound(file_path).get_length()
            mixer.music.play()
            self.playing = True

            self.log_message(f"▶️ Playing: {os.path.basename(file_path)}")
            self.play_thread = Thread(target=self._track_cursor, args=(duration,))
            self.play_thread.start()
        except Exception as e:
            self.log_message(f"⚠️ Playback error: {e}")
            self.playing = False

    def _track_cursor(self, duration):
        steps = 100  # Cursor resolution
        delay = duration / steps

        for i in range(steps):
            if not self.playing:
                break
            self._send_cursor_position(i / steps)
            sleep(delay)

        self._send_cursor_position(0)
        self.playing = False

    def _send_cursor_position(self, percent):
        # This can be hooked into GUI later
        self.log_message(f"🕒 Cursor: {int(percent * 100)}%")

    def _maybe_generate_waveform(self):
        file_path = self.config.get("file_path", "")
        if not file_path or not os.path.isfile(file_path):
            return

        waveform_path = file_path + ".waveform.png"
        if os.path.exists(waveform_path):
            self.waveform_image_path = waveform_path
            return

        try:
            from pydub import AudioSegment  # <--- moved inside
            audio = AudioSegment.from_file(file_path)
            samples = np.array(audio.get_array_of_samples())

            import matplotlib.pyplot as plt
            plt.figure(figsize=(8, 2))
            plt.plot(samples, color='black')
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(waveform_path, bbox_inches='tight', pad_inches=0)
            plt.close()

            self.waveform_image_path = waveform_path
            self.log_message("📈 Waveform generated.")
        except Exception as e:
            self.log_message(f"⚠️ Failed to generate waveform: {e}")
