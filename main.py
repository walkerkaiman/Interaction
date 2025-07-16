"""
Interaction - Interactive Art Installation Framework
Main Application Entry Point

This file implements a singleton pattern to ensure only one instance of the
Interaction application can run at a time. This prevents port conflicts,
resource contention, and data corruption that can occur with multiple instances.

The singleton pattern uses a lock file mechanism:
1. Check if a lock file exists
2. If it exists, verify if the process is still running
3. If the process is dead, remove the stale lock file
4. If the process is alive, prevent startup
5. If no lock file exists, create one and start the application
6. Clean up the lock file on exit

Author: Interaction Framework Team
License: MIT
"""

import os
import sys
import socket
import argparse
import threading
import time
import webbrowser
from pathlib import Path

# Performance optimization imports - Integrated from performance package
from module_loader import get_thread_pool, shutdown_global_thread_pool, get_config_cache, shutdown_config_cache
from message_router import get_message_router, shutdown_message_router
from modules.audio_output.audio_output import get_audio_processor, shutdown_audio_processor

# High-Performance Performance Manager - Integrated from performance package
import threading
import time
import psutil
import gc
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

class PerformanceLevel(Enum):
    """Performance optimization levels"""
    MAXIMUM = "maximum"      # All optimizations enabled
    BALANCED = "balanced"    # Balanced performance and compatibility
    CONSERVATIVE = "conservative"  # Minimal optimizations for stability
    DISABLED = "disabled"    # All optimizations disabled

@dataclass
class PerformanceMetrics:
    """Performance metrics snapshot"""
    timestamp: float
    cpu_usage: float
    memory_usage: float
    thread_count: int
    event_latency: float
    cache_hit_rate: float
    events_per_second: int
    optimization_level: str

class PerformanceManager:
    """
    Unified performance management system.
    
    This class coordinates all performance optimizations and provides
    real-time monitoring and adjustment capabilities. It ensures optimal
    performance while maintaining the event-based, reactive architecture.
    """
    
    def __init__(self, optimization_level: PerformanceLevel = PerformanceLevel.BALANCED):
        """
        Initialize the performance manager.
        
        Args:
            optimization_level: Initial optimization level
        """
        self.optimization_level = optimization_level
        self.enabled = optimization_level != PerformanceLevel.DISABLED
        
        # Performance monitoring
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self.monitoring_interval = 1.0
        
        # Component references
        self.thread_pool = None
        self.config_cache = None
        self.message_router = None
        self.audio_processor = None
        
        # Performance thresholds
        self.cpu_threshold = 80.0  # CPU usage threshold (%)
        self.memory_threshold = 80.0  # Memory usage threshold (%)
        self.latency_threshold = 0.010  # 10ms latency threshold
        
        # Callbacks for performance alerts
        self.performance_callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        # Monitoring thread
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        
        # Initialize components if optimizations are enabled
        if self.enabled:
            self._initialize_components()
            self._start_monitoring()
    
    def _initialize_components(self):
        """Initialize optimized components based on optimization level"""
        if self.optimization_level == PerformanceLevel.DISABLED:
            return
        
        try:
            # Initialize thread pool
            self.thread_pool = get_thread_pool()
            print(f"✅ Thread pool initialized with {self.thread_pool.max_threads} max threads")
            
            # Initialize configuration cache
            self.config_cache = get_config_cache()
            print("✅ Configuration cache initialized")
            
            # Initialize optimized message router
            if self.optimization_level in [PerformanceLevel.MAXIMUM, PerformanceLevel.BALANCED]:
                self.message_router = get_message_router()
                print("✅ Optimized message router initialized")
            
            # Initialize audio processor
            self.audio_processor = get_audio_processor()
            print("✅ Optimized audio processor initialized")
            
        except Exception as e:
            print(f"❌ Error initializing performance components: {e}")
            self.enabled = False
    
    def _start_monitoring(self):
        """Start performance monitoring thread"""
        if not self.enabled:
            return
        
        self.monitoring_thread = threading.Thread(
            target=self._monitor_performance,
            name="PerformanceMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
        print("✅ Performance monitoring started")
    
    def _monitor_performance(self):
        """Monitor performance metrics continuously"""
        while not self.stop_monitoring.is_set():
            try:
                # Collect metrics
                metrics = self._collect_metrics()
                
                # Store metrics
                self.metrics_history.append(metrics)
                
                # Trim history if too large
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                
                # Check thresholds and trigger callbacks
                self._check_performance_thresholds(metrics)
                
                # Auto-adjust optimization level if needed
                self._auto_adjust_optimization(metrics)
                
            except Exception as e:
                print(f"❌ Error in performance monitoring: {e}")
            
            self.stop_monitoring.wait(self.monitoring_interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics"""
        # System metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        thread_count = threading.active_count()
        
        # Component metrics
        cache_hit_rate = 0.0
        event_latency = 0.0
        events_per_second = 0
        
        if self.config_cache:
            cache_stats = self.config_cache.get_stats()
            cache_hit_rate = cache_stats.get("hit_rate", 0.0)
        
        if self.message_router:
            router_stats = self.message_router.get_stats()
            event_latency = router_stats.get("avg_latency_ms", 0.0) / 1000.0  # Convert to seconds
            events_per_second = router_stats.get("events_routed", 0)
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            thread_count=thread_count,
            event_latency=event_latency,
            cache_hit_rate=cache_hit_rate,
            events_per_second=events_per_second,
            optimization_level=self.optimization_level.value
        )
    
    def _check_performance_thresholds(self, metrics: PerformanceMetrics):
        """Check if performance thresholds are exceeded"""
        alerts = []
        
        if metrics.cpu_usage > self.cpu_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        
        if metrics.memory_usage > self.memory_threshold:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        
        if metrics.event_latency > self.latency_threshold:
            alerts.append(f"High event latency: {metrics.event_latency*1000:.1f}ms")
        
        # Trigger callbacks for alerts
        if alerts:
            for callback in self.performance_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    print(f"❌ Error in performance callback: {e}")
    
    def _auto_adjust_optimization(self, metrics: PerformanceMetrics):
        """Automatically adjust optimization level based on performance"""
        if metrics.cpu_usage > 90.0 or metrics.memory_usage > 90.0:
            # Reduce optimization level under high load
            if self.optimization_level == PerformanceLevel.MAXIMUM:
                self.set_optimization_level(PerformanceLevel.BALANCED)
        elif metrics.cpu_usage < 30.0 and metrics.memory_usage < 50.0:
            # Increase optimization level under low load
            if self.optimization_level == PerformanceLevel.CONSERVATIVE:
                self.set_optimization_level(PerformanceLevel.BALANCED)
    
    def set_optimization_level(self, level: PerformanceLevel):
        """Set the optimization level"""
        if level == self.optimization_level:
            return
        
        print(f"🔄 Changing optimization level from {self.optimization_level.value} to {level.value}")
        
        # Shutdown current components
        self._shutdown_components()
        
        # Update level
        self.optimization_level = level
        self.enabled = level != PerformanceLevel.DISABLED
        
        # Reinitialize components
        if self.enabled:
            self._initialize_components()
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, duration_seconds: float = 60.0) -> List[PerformanceMetrics]:
        """Get performance metrics from the last N seconds"""
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary"""
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {"status": "No metrics available"}
        
        # Calculate averages from recent history
        recent_metrics = self.get_metrics_history(60.0)  # Last minute
        if recent_metrics:
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_latency = sum(m.event_latency for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = avg_memory = avg_latency = 0.0
        
        return {
            "optimization_level": self.optimization_level.value,
            "enabled": self.enabled,
            "current_metrics": asdict(current_metrics),
            "averages_1min": {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "event_latency_ms": avg_latency * 1000
            },
            "component_status": {
                "thread_pool": self.thread_pool is not None,
                "config_cache": self.config_cache is not None,
                "message_router": self.message_router is not None,
                "audio_processor": self.audio_processor is not None
            }
        }
    
    def add_performance_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Add a callback for performance alerts"""
        self.performance_callbacks.append(callback)
    
    def remove_performance_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """Remove a performance callback"""
        if callback in self.performance_callbacks:
            self.performance_callbacks.remove(callback)
    
    def force_optimization(self, component: str):
        """Force optimization of a specific component"""
        if component == "thread_pool" and not self.thread_pool:
            self.thread_pool = get_thread_pool()
            print("✅ Thread pool forced initialization")
        elif component == "config_cache" and not self.config_cache:
            self.config_cache = get_config_cache()
            print("✅ Config cache forced initialization")
        elif component == "message_router" and not self.message_router:
            self.message_router = get_message_router()
            print("✅ Message router forced initialization")
        elif component == "audio_processor" and not self.audio_processor:
            self.audio_processor = get_audio_processor()
            print("✅ Audio processor forced initialization")
    
    def _shutdown_components(self):
        """Shutdown performance components"""
        if self.message_router:
            shutdown_message_router()
            self.message_router = None
        
        if self.audio_processor:
            shutdown_audio_processor()
            self.audio_processor = None
    
    def shutdown(self):
        """Shutdown the performance manager"""
        print("🛑 Shutting down performance manager...")
        
        # Stop monitoring
        self.stop_monitoring.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        
        # Shutdown components
        self._shutdown_components()
        
        # Clear callbacks
        self.performance_callbacks.clear()
        
        print("✅ Performance manager shutdown complete")

# Global performance manager instance
_global_performance_manager = None

def get_performance_manager() -> Optional[PerformanceManager]:
    """Get the global performance manager instance"""
    global _global_performance_manager
    return _global_performance_manager

def initialize_performance_optimizations(level: PerformanceLevel = PerformanceLevel.BALANCED) -> PerformanceManager:
    """Initialize performance optimizations"""
    global _global_performance_manager
    if _global_performance_manager is None:
        _global_performance_manager = PerformanceManager(level)
    return _global_performance_manager

def shutdown_performance_manager():
    """Shutdown the global performance manager"""
    global _global_performance_manager
    if _global_performance_manager:
        _global_performance_manager.shutdown()
        _global_performance_manager = None

# Optionally import Tkinter GUI
try:
    from gui import launch_gui
except ImportError:
    launch_gui = None

def is_port_in_use(port):
    """
    Check if a specific port is in use by attempting to bind to it.
    
    Args:
        port (int): Port number to check
        
    Returns:
        bool: True if port is in use, False if available
        
    Note: This is a utility function for port availability checking,
    though the main singleton mechanism uses lock files instead.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return False
        except OSError:
            return True

def create_lock_file():
    """
    Create a lock file to indicate the application is running.
    
    The lock file contains the current process ID (PID) so we can
    verify if the process is still alive later.
    
    Returns:
        str: Path to the created lock file, or None if creation failed
        
    Note: The lock file is created in the current working directory
    and named 'interaction_app.lock'.
    """
    lock_file = "interaction_app.lock"
    try:
        # Write the current process ID to the lock file
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
        return lock_file
    except Exception:
        return None

def remove_lock_file(lock_file):
    """
    Remove the lock file to indicate the application has stopped.
    
    Args:
        lock_file (str): Path to the lock file to remove
        
    Note: This function is called during cleanup to ensure the lock file
    is removed even if the application crashes or is forcefully terminated.
    """
    try:
        if lock_file and os.path.exists(lock_file):
            os.remove(lock_file)
    except Exception:
        pass

def check_singleton():
    """
    Check if another instance of the application is already running.
    
    This function implements the core singleton logic:
    1. Check if the lock file exists
    2. If it exists, read the PID and verify the process is alive
    3. If the process is dead, remove the stale lock file
    4. If the process is alive, prevent startup
    5. If no lock file exists, allow startup
    
    Returns:
        bool: True if no other instance is running, False otherwise
        
    Note: This prevents multiple instances from running simultaneously,
    which would cause port conflicts and resource contention.
    """
    lock_file = "interaction_app.lock"
    
    # Check if lock file exists
    if os.path.exists(lock_file):
        try:
            # Read the PID from the lock file
            with open(lock_file, 'r') as f:
                pid_str = f.read().strip()
                if pid_str.isdigit():
                    pid = int(pid_str)
                    # Check if the process is still running
                    try:
                        # os.kill(pid, 0) sends signal 0 (no signal) to check if process exists
                        # This will raise an OSError if the process doesn't exist
                        os.kill(pid, 0)
                        print(f"❌ Another instance of Interaction App is already running (PID: {pid})")
                        print("Please close the existing instance before starting a new one.")
                        return False
                    except OSError:
                        # Process doesn't exist, remove stale lock file
                        print("🔄 Removing stale lock file from previous instance")
                        remove_lock_file(lock_file)
        except Exception:
            # Lock file is corrupted, remove it
            print("🔄 Removing corrupted lock file")
            remove_lock_file(lock_file)
    
    return True

def main():
    print("🚀 Starting Interaction App...")
    # Initialize performance optimizations
    perf_manager = initialize_performance_optimizations(PerformanceLevel.BALANCED)
    parser = argparse.ArgumentParser(description="Interaction App Backend")
    parser.add_argument('--web', action='store_true', help='Start the web backend (default)')
    parser.add_argument('--gui', action='store_true', help='Start the legacy Tkinter GUI')
    args = parser.parse_args()

    if not check_singleton():
        input("Press Enter to exit...")
        sys.exit(1)
    lock_file = create_lock_file()
    if not lock_file:
        print("❌ Failed to create lock file. Another instance might be running.")
        input("Press Enter to exit...")
        sys.exit(1)
    try:
        if args.gui and launch_gui:
            print("✅ Starting legacy GUI...")
            launch_gui()
        else:
            print("✅ Starting web backend...")
            
            # Get the path to the web interface
            web_gui_path = Path(__file__).parent / "web-frontend" / "simple-gui.html"
            
            # Check if the web GUI file exists
            if not web_gui_path.exists():
                print(f"⚠️  Web GUI file not found at: {web_gui_path}")
                print("Starting backend without web interface...")
                import web_backend
                web_backend.run()
            else:
                # Start the web backend in a separate thread using optimized thread pool
                def start_web_backend():
                    import web_backend
                    web_backend.run()
                
                thread_pool = get_thread_pool()
                backend_thread = thread_pool.submit_realtime(start_web_backend)
                
                # Wait a moment for the server to start
                print("⏳ Waiting for server to start...")
                time.sleep(3)
                
                # Open the web interface in the default browser
                print("🌐 Opening web interface...")
                try:
                    webbrowser.open(f"file://{web_gui_path}")
                    print("✅ Web interface opened in browser!")
                    print("🔗 Manual URL: file://" + str(web_gui_path))
                except Exception as e:
                    print(f"⚠️  Could not open browser automatically: {e}")
                    print("🔗 Please manually open: file://" + str(web_gui_path))
                
                print("🛑 Press Ctrl+C to stop the server")
                
                # Keep the main thread running
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n🛑 Stopping web backend...")
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
    except Exception as e:
        print(f"💥 Application error: {e}")
    finally:
        remove_lock_file(lock_file)
        shutdown_performance_manager()
        print("👋 Interaction App closed")

if __name__ == "__main__":
    main()