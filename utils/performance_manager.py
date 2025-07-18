import threading
import time
import psutil
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum

class PerformanceLevel(Enum):
    """Performance optimization levels"""
    MAXIMUM = "maximum"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    DISABLED = "disabled"

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
    Coordinates all performance optimizations and provides real-time monitoring and adjustment.
    """
    def __init__(self, optimization_level: PerformanceLevel = PerformanceLevel.BALANCED):
        self.optimization_level = optimization_level
        self.enabled = optimization_level != PerformanceLevel.DISABLED
        self.metrics_history: List[PerformanceMetrics] = []
        self.max_history_size = 1000
        self.monitoring_interval = 1.0
        self.thread_pool = None
        self.config_cache = None
        self.message_router = None
        self.audio_processor = None
        self.cpu_threshold = 80.0
        self.memory_threshold = 80.0
        self.latency_threshold = 0.010
        self.performance_callbacks: List[Callable[[PerformanceMetrics], None]] = []
        self.monitoring_thread = None
        self.stop_monitoring = threading.Event()
        if self.enabled:
            self._initialize_components()
            self._start_monitoring()
    def _initialize_components(self):
        from utils.thread_pool_utils import get_thread_pool
        from module_loader import get_config_cache
        from message_router import get_message_router
        from modules.audio_output.audio_output import get_audio_processor
        if self.optimization_level == PerformanceLevel.DISABLED:
            return
        try:
            self.thread_pool = get_thread_pool()
            self.config_cache = get_config_cache()
            if self.optimization_level in [PerformanceLevel.MAXIMUM, PerformanceLevel.BALANCED]:
                self.message_router = get_message_router()
            self.audio_processor = get_audio_processor()
        except Exception:
            self.enabled = False
    def _start_monitoring(self):
        if not self.enabled:
            return
        self.monitoring_thread = threading.Thread(
            target=self._monitor_performance,
            name="PerformanceMonitor",
            daemon=True
        )
        self.monitoring_thread.start()
    def _monitor_performance(self):
        while not self.stop_monitoring.is_set():
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                if len(self.metrics_history) > self.max_history_size:
                    self.metrics_history.pop(0)
                self._check_performance_thresholds(metrics)
                self._auto_adjust_optimization(metrics)
            except Exception:
                pass
            self.stop_monitoring.wait(self.monitoring_interval)
    def _collect_metrics(self) -> PerformanceMetrics:
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        thread_count = threading.active_count()
        cache_hit_rate = 0.0
        event_latency = 0.0
        events_per_second = 0
        if self.config_cache:
            cache_stats = self.config_cache.get_stats()
            cache_hit_rate = cache_stats.get("hit_rate", 0.0)
        if self.message_router:
            router_stats = self.message_router.get_stats()
            event_latency = router_stats.get("avg_latency_ms", 0.0) / 1000.0
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
        alerts = []
        if metrics.cpu_usage > self.cpu_threshold:
            alerts.append(f"High CPU usage: {metrics.cpu_usage:.1f}%")
        if metrics.memory_usage > self.memory_threshold:
            alerts.append(f"High memory usage: {metrics.memory_usage:.1f}%")
        if metrics.event_latency > self.latency_threshold:
            alerts.append(f"High event latency: {metrics.event_latency*1000:.1f}ms")
        if alerts:
            for callback in self.performance_callbacks:
                try:
                    callback(metrics)
                except Exception:
                    pass
    def _auto_adjust_optimization(self, metrics: PerformanceMetrics):
        if metrics.cpu_usage > 90.0 or metrics.memory_usage > 90.0:
            if self.optimization_level == PerformanceLevel.MAXIMUM:
                self.set_optimization_level(PerformanceLevel.BALANCED)
        elif metrics.cpu_usage < 30.0 and metrics.memory_usage < 50.0:
            if self.optimization_level == PerformanceLevel.CONSERVATIVE:
                self.set_optimization_level(PerformanceLevel.BALANCED)
    def set_optimization_level(self, level: PerformanceLevel):
        if level == self.optimization_level:
            return
        self._shutdown_components()
        self.optimization_level = level
        self.enabled = level != PerformanceLevel.DISABLED
        if self.enabled:
            self._initialize_components()
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    def get_metrics_history(self, duration_seconds: float = 60.0) -> List[PerformanceMetrics]:
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    def get_performance_summary(self) -> Dict[str, Any]:
        current_metrics = self.get_current_metrics()
        if not current_metrics:
            return {"status": "No metrics available"}
        recent_metrics = self.get_metrics_history(60.0)
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
        self.performance_callbacks.append(callback)
    def remove_performance_callback(self, callback: Callable[[PerformanceMetrics], None]):
        if callback in self.performance_callbacks:
            self.performance_callbacks.remove(callback)
    def force_optimization(self, component: str):
        from utils.thread_pool_utils import get_thread_pool
        from module_loader import get_config_cache
        from message_router import get_message_router
        from modules.audio_output.audio_output import get_audio_processor
        if component == "thread_pool" and not self.thread_pool:
            self.thread_pool = get_thread_pool()
        elif component == "config_cache" and not self.config_cache:
            self.config_cache = get_config_cache()
        elif component == "message_router" and not self.message_router:
            self.message_router = get_message_router()
        elif component == "audio_processor" and not self.audio_processor:
            self.audio_processor = get_audio_processor()
    def _shutdown_components(self):
        from message_router import shutdown_message_router
        from modules.audio_output.audio_output import shutdown_audio_processor
        if self.message_router:
            shutdown_message_router()
            self.message_router = None
        if self.audio_processor:
            shutdown_audio_processor()
            self.audio_processor = None
    def shutdown(self):
        self.stop_monitoring.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        self._shutdown_components()
        self.performance_callbacks.clear()

_global_performance_manager = None

def get_performance_manager() -> Optional[PerformanceManager]:
    global _global_performance_manager
    return _global_performance_manager

def initialize_performance_optimizations(level: PerformanceLevel = PerformanceLevel.BALANCED) -> PerformanceManager:
    global _global_performance_manager
    if _global_performance_manager is None:
        _global_performance_manager = PerformanceManager(level)
    return _global_performance_manager

def shutdown_performance_manager():
    global _global_performance_manager
    if _global_performance_manager:
        _global_performance_manager.shutdown()
        _global_performance_manager = None 