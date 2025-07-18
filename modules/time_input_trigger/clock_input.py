import threading
import time
from datetime import datetime, timedelta
from modules.module_base import DedicatedThreadModule
import uuid

class TimeInputModule(DedicatedThreadModule):
    def __init__(self, config, manifest, log_callback=None, strategy=None):
        def silent_log_callback(msg):
            if msg.startswith("Emitting event:"):
                return
            if '❌' in msg or '🛑' in msg:
                print(msg)
        super().__init__(config, manifest, log_callback=log_callback or silent_log_callback, strategy=strategy)
        self.instance_id = str(uuid.uuid4())
        self.target_time = config.get('target_time', '')
        # Thread/event management handled by DedicatedThreadModule
        self.log_message(f"Time Input initialized - Target: {self.target_time}")

    # start/stop/wait_for_stop handled by DedicatedThreadModule

    # wait_for_stop handled by DedicatedThreadModule

    def _run(self):
        print(f"[THREAD DEBUG] TimeInputModule._run called for {self.__class__}")
        while self._running and not self._stop_event.is_set():
            try:
                current_time = datetime.now()
                current_time_str = current_time.strftime('%H:%M:%S')
                countdown_str = "--:--:--"
                if self.target_time:
                    try:
                        target_dt = datetime.strptime(self.target_time, '%H:%M:%S')
                        target_dt = current_time.replace(
                            hour=target_dt.hour,
                            minute=target_dt.minute,
                            second=target_dt.second,
                            microsecond=0
                        )
                        if target_dt <= current_time:
                            target_dt += timedelta(days=1)
                        time_diff = target_dt - current_time
                        total_seconds = int(time_diff.total_seconds())
                        if total_seconds > 0:
                            hours = total_seconds // 3600
                            minutes = (total_seconds % 3600) // 60
                            seconds = total_seconds % 60
                            countdown_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        else:
                            countdown_str = "00:00:00"
                    except ValueError:
                        countdown_str = "Invalid time"
                event_data = {
                    "current_time": current_time_str,
                    "countdown": countdown_str,
                    "target_time": self.target_time
                }
                if countdown_str == "00:00:00" and self.target_time:
                    event_data["trigger"] = True
                event_data['instance_id'] = self.instance_id
                self.log_message(f"[DEBUG] Emitting event from instance {self.instance_id} with target_time={self.target_time}")
                self.emit_event(event_data)
                now = datetime.now()
                next_second = now.replace(microsecond=0) + timedelta(seconds=1)
                wait_time = (next_second - now).total_seconds()
                self._stop_event.wait(wait_time)
            except Exception as e:
                self.log_message(f"❌ Error in time input loop: {e}")
                if self._running and not self._stop_event.is_set():
                    self._stop_event.wait(1)

    def update_config(self, config):
        old_target = self.target_time
        self.target_time = config.get('target_time', self.target_time)
        if old_target != self.target_time:
            self.log_message(f"🔄 Target time updated: {self.target_time}")

    def auto_configure(self):
        if not getattr(self, 'target_time', None):
            self.target_time = '12:00:00'
            self.config['target_time'] = '12:00:00'
            self.log_message("[Auto-configure] Set default target time: 12:00:00")

    def get_display_data(self):
        current_time = datetime.now().strftime('%H:%M:%S')
        return {
            'current_time': current_time,
            'countdown': '--:--:--'
        } 