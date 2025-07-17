import threading
import time
from datetime import datetime, timedelta
from modules.module_base import ModuleBase
from module_loader import get_thread_pool
import uuid

class ClockInputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print, strategy=None):
        super().__init__(config, manifest, log_callback, strategy=strategy)
        self.instance_id = str(uuid.uuid4())  # Unique ID for debugging
        
        # Time configuration
        self.target_time = config.get('target_time', '')
        self.time_format = config.get('time_format', '%H:%M:%S')
        
        # Thread management
        self._thread = None
        self._running = False
        
        # Get optimized thread pool
        self.thread_pool = get_thread_pool()
        
        self.log_message(f"Clock Input initialized - Target: {self.target_time}")

    def start(self):
        super().start()
        if not self._running:
            self._running = True
            # Use optimized thread pool instead of creating new thread
            self._thread = self.thread_pool.submit_realtime(self._run)
            self.log_message("🕐 Clock input started")

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.cancel()  # Cancel the thread pool task
        super().stop()
        self.wait_for_stop()
        self.log_message(f"🛑 Clock input stopped (instance {self.instance_id})")

    def wait_for_stop(self):
        """
        Wait for the clock thread to finish.
        """
        if self._thread and hasattr(self._thread, 'result'):
            try:
                self._thread.result(timeout=1)
            except Exception:
                pass
        self._thread = None

    def _run(self):
        """Main clock loop - optimized to use event-driven approach instead of sleep"""
        while self._running:
            try:
                current_time = datetime.now()
                current_time_str = current_time.strftime(self.time_format)
                
                # Calculate countdown if target time is set
                countdown_str = "--:--:--"
                if self.target_time:
                    try:
                        target_dt = datetime.strptime(self.target_time, self.time_format)
                        # Set target to today with the specified time
                        target_dt = current_time.replace(
                            hour=target_dt.hour,
                            minute=target_dt.minute,
                            second=target_dt.second,
                            microsecond=0
                        )
                        
                        # If target time has passed today, set it to tomorrow
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
                
                # Create event data
                event_data = {
                    "current_time": current_time_str,
                    "countdown": countdown_str,
                    "target_time": self.target_time
                }
                
                # Check if we should trigger (when countdown reaches zero)
                if countdown_str == "00:00:00" and self.target_time:
                    event_data["trigger"] = True
                
                # Emit the event
                event_data['instance_id'] = self.instance_id  # For debugging
                self.emit_event(event_data)
                
                # Use event-driven approach: wait for next second boundary
                # Instead of sleep(1), calculate time to next second
                now = datetime.now()
                next_second = now.replace(microsecond=0) + timedelta(seconds=1)
                wait_time = (next_second - now).total_seconds()
                
                if wait_time > 0 and self._running:
                    # Use threading.Event for precise timing instead of sleep
                    event = threading.Event()
                    event.wait(wait_time)
                
            except Exception as e:
                self.log_message(f"❌ Error in clock loop: {e}")
                # Brief pause on error to prevent tight loop
                if self._running:
                    threading.Event().wait(1)

    def update_config(self, config):
        """Update the module configuration"""
        old_target = self.target_time
        self.target_time = config.get('target_time', self.target_time)
        self.time_format = config.get('time_format', self.time_format)
        
        if old_target != self.target_time:
            self.log_message(f"🔄 Target time updated: {self.target_time}")

    def auto_configure(self):
        """Set default target time if none is configured"""
        if not getattr(self, 'target_time', None):
            self.target_time = '12:00:00'
            self.config['target_time'] = '12:00:00'
            self.log_message("[Auto-configure] Set default target time: 12:00:00")

    def get_display_data(self):
        """Return data for GUI display fields"""
        current_time = datetime.now().strftime(self.time_format)
        return {
            'current_time': current_time,
            'countdown': '--:--:--'  # Will be calculated in the main loop
        } 