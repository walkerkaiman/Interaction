import threading
import time
from datetime import datetime, timedelta
from modules.module_base import ModuleBase

class ClockInputModule(ModuleBase):
    def __init__(self, config, manifest, log_callback=print):
        super().__init__(config, manifest, log_callback)
        self.target_time = config.get('target_time', '12:00:00')
        self.current_time = None
        self.countdown = None
        self._running = False
        self._thread = None
        self._event_callbacks = set()
        self._last_fired = None

    def start(self):
        super().start()  # Ensure state transitions and EventRouter notifications
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Stop the clock input module and clean up resources.
        Ensures all threads and resources are properly released.
        """
        self._running = False
        if self._thread:
            self.log_callback("[DEBUG] Joining clock input thread...")
            self._thread.join(timeout=2)
            self._thread = None
        self.log_callback("🛑 Clock input module stopped")

    def add_event_callback(self, callback):
        self._event_callbacks.add(callback)

    def remove_event_callback(self, callback):
        self._event_callbacks.discard(callback)

    def update_config(self, config):
        old_target = self.target_time
        self.target_time = config.get('target_time', self.target_time)
        self.log_callback(f"🔄 Clock: update_config called with config: {config}")
        self.log_callback(f"🔄 Clock: Target time updated from {old_target} to {self.target_time}")
        # Optionally reset last fired so it can fire again if target changes
        self._last_fired = None

    def auto_configure(self):
        """
        If no target_time is set, set it to now + 1 hour.
        """
        import datetime
        if not getattr(self, 'target_time', None):
            now = datetime.datetime.now()
            target = now + datetime.timedelta(hours=1)
            self.target_time = target.strftime('%H:%M:%S')
            self.config['target_time'] = self.target_time
            self.log_message(f"[Auto-configure] Set default target_time: {self.target_time}")

    def _calculate_countdown(self, current_time_str, target_time_str):
        """Calculate the time difference between current and target time."""
        try:
            # Parse current time
            current_dt = datetime.strptime(current_time_str, '%H:%M:%S').replace(
                year=datetime.now().year, 
                month=datetime.now().month, 
                day=datetime.now().day
            )
            
            # Parse target time
            target_dt = datetime.strptime(target_time_str, '%H:%M:%S').replace(
                year=datetime.now().year, 
                month=datetime.now().month, 
                day=datetime.now().day
            )
            
            # If target time is earlier today, assume it's for tomorrow
            if target_dt <= current_dt:
                target_dt += timedelta(days=1)
            
            # Calculate difference
            time_diff = target_dt - current_dt
            total_seconds = int(time_diff.total_seconds())
            
            if total_seconds <= 0:
                return "00:00:00"
            
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            self.log_callback(f"⚠️ Error calculating countdown: {e}")
            return "--:--:--"

    def _run(self):
        while self._running:
            now = datetime.now().strftime('%H:%M:%S')
            self.current_time = now
            
            # Calculate countdown
            self.countdown = self._calculate_countdown(now, self.target_time)
            
            # Update the GUI display if available
            if hasattr(self, 'update_display'):
                self.update_display()
            
            # Always emit event for current time and countdown (event-driven GUI update)
            event = {
                'current_time': self.current_time,
                'countdown': self.countdown,
                'timestamp': time.time(),
                'trigger': False
            }
            for cb in list(self._event_callbacks):
                try:
                    cb(event)
                except Exception as e:
                    self.log_callback(f"⚠️ Error in clock event callback: {e}")
            
            # Check if target time matches current time
            if self.target_time == now and self._last_fired != now:
                self.log_callback(f"🎯 Clock: Target time {self.target_time} matches current time {now} - firing event!")
                event = {
                    'current_time': now,
                    'target_time': self.target_time,
                    'countdown': self.countdown,
                    'timestamp': time.time(),
                    'trigger': True
                }
                for cb in list(self._event_callbacks):
                    try:
                        cb(event)
                    except Exception as e:
                        self.log_callback(f"⚠️ Error in clock event callback: {e}")
                self._last_fired = now
            time.sleep(1)  # Update every second

    def update_display(self):
        """Update the GUI display with current time."""
        # This method can be called by the GUI to update the current time label
        pass

    def get_display_data(self):
        """Return data for GUI display fields."""
        return {
            'current_time': self.current_time or '--:--:--',
            'target_time': self.target_time,
            'countdown': self.countdown or '--:--:--'
        } 

    def emit_current_state(self):
        """Immediately emit the current time and countdown to all registered callbacks (trigger: False)."""
        now = datetime.now().strftime('%H:%M:%S')
        self.current_time = now
        self.countdown = self._calculate_countdown(now, self.target_time)
        event = {
            'current_time': self.current_time,
            'countdown': self.countdown,
            'timestamp': time.time(),
            'trigger': False
        }
        for cb in list(self._event_callbacks):
            try:
                cb(event)
            except Exception as e:
                self.log_callback(f"⚠️ Error in clock event callback: {e}") 

    def _on_time_reached(self, target_time, current_time):
        # Called when the target time is reached
        event_data = {
            'target_time': target_time,
            'current_time': current_time,
            'triggered': True
        }
        self.emit_event(event_data)
        self.log_message(f"Clock Input emitting event: {event_data}") 