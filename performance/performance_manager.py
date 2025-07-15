"""
Performance Manager - Unified Performance Optimization Coordinator

This module provides a unified interface for all performance optimizations in the
Interactive Art Installation Framework. It coordinates thread pools, caching,
message routing, and audio processing to deliver optimal performance.

Key Features:
- Unified performance management interface
- Automatic optimization detection and configuration
- Real-time performance monitoring and reporting
- Resource usage optimization
- Graceful degradation under load
- Performance statistics and analytics

Author: Interaction Framework Team
License: MIT
"""

import threading
import time
import psutil
import gc
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json

# Import our optimized components
from performance.thread_pool import get_thread_pool, shutdown_global_thread_pool
from performance.config_cache import get_config_cache, shutdown_config_cache
from performance.optimized_message_router import get_message_router, shutdown_message_router
from performance.optimized_audio_processing import get_audio_processor, shutdown_audio_processor

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
            event_latency = router_stats.get("avg_latency", 0.0)
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
        
        if alerts:
            print(f"⚠️ Performance alerts: {', '.join(alerts)}")
            
            # Trigger callbacks
            for callback in self.performance_callbacks:
                try:
                    callback(metrics)
                except Exception as e:
                    print(f"❌ Error in performance callback: {e}")
    
    def _auto_adjust_optimization(self, metrics: PerformanceMetrics):
        """Automatically adjust optimization level based on performance"""
        if not self.enabled:
            return
        
        # Auto-scale based on system load
        if metrics.cpu_usage > 90 or metrics.memory_usage > 90:
            # System under high load - trigger garbage collection
            gc.collect()
            
            # Consider reducing optimization level
            if self.optimization_level == PerformanceLevel.MAXIMUM:
                self.set_optimization_level(PerformanceLevel.BALANCED)
                print("🔧 Auto-adjusted to BALANCED optimization due to high system load")
        
        elif metrics.cpu_usage < 30 and metrics.memory_usage < 50:
            # System has resources available - can increase optimization
            if self.optimization_level == PerformanceLevel.BALANCED:
                self.set_optimization_level(PerformanceLevel.MAXIMUM)
                print("🔧 Auto-adjusted to MAXIMUM optimization due to available resources")
    
    def set_optimization_level(self, level: PerformanceLevel):
        """
        Set the optimization level.
        
        Args:
            level: New optimization level
        """
        if level == self.optimization_level:
            return
        
        old_level = self.optimization_level
        self.optimization_level = level
        
        if level == PerformanceLevel.DISABLED:
            self.enabled = False
            self._shutdown_components()
        else:
            if not self.enabled:
                self.enabled = True
                self._initialize_components()
        
        print(f"🔧 Optimization level changed from {old_level.value} to {level.value}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics"""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_metrics_history(self, duration_seconds: float = 60.0) -> List[PerformanceMetrics]:
        """
        Get performance metrics history for a specified duration.
        
        Args:
            duration_seconds: Duration in seconds to retrieve
            
        Returns:
            List of performance metrics
        """
        cutoff_time = time.time() - duration_seconds
        return [m for m in self.metrics_history if m.timestamp >= cutoff_time]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance status"""
        current_metrics = self.get_current_metrics()
        
        if not current_metrics:
            return {"status": "no_data", "enabled": self.enabled}
        
        # Calculate averages over last minute
        recent_metrics = self.get_metrics_history(60.0)
        
        if recent_metrics:
            avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
            avg_latency = sum(m.event_latency for m in recent_metrics) / len(recent_metrics)
        else:
            avg_cpu = current_metrics.cpu_usage
            avg_memory = current_metrics.memory_usage
            avg_latency = current_metrics.event_latency
        
        # Get component statistics
        component_stats = {}
        
        if self.thread_pool:
            component_stats["thread_pool"] = self.thread_pool.get_stats()
        
        if self.config_cache:
            component_stats["config_cache"] = self.config_cache.get_stats()
        
        if self.message_router:
            component_stats["message_router"] = self.message_router.get_stats()
        
        if self.audio_processor:
            component_stats["audio_processor"] = self.audio_processor.get_stats()
        
        return {
            "status": "active" if self.enabled else "disabled",
            "optimization_level": self.optimization_level.value,
            "current_metrics": asdict(current_metrics),
            "averages": {
                "cpu_usage": avg_cpu,
                "memory_usage": avg_memory,
                "event_latency": avg_latency
            },
            "component_stats": component_stats,
            "thresholds": {
                "cpu_threshold": self.cpu_threshold,
                "memory_threshold": self.memory_threshold,
                "latency_threshold": self.latency_threshold
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
        """Force optimization for a specific component"""
        if not self.enabled:
            print("⚠️ Performance optimizations are disabled")
            return
        
        if component == "thread_pool" and self.thread_pool:
            # Force thread pool optimization
            stats = self.thread_pool.get_stats()
            print(f"🔧 Thread pool stats: {stats}")
        
        elif component == "config_cache" and self.config_cache:
            # Force cache cleanup
            cache_stats = self.config_cache.get_stats()
            print(f"🔧 Config cache stats: {cache_stats}")
        
        elif component == "message_router" and self.message_router:
            # Force router optimization
            router_stats = self.message_router.get_stats()
            print(f"🔧 Message router stats: {router_stats}")
        
        elif component == "audio_processor" and self.audio_processor:
            # Force audio processor optimization
            audio_stats = self.audio_processor.get_stats()
            print(f"🔧 Audio processor stats: {audio_stats}")
        
        elif component == "garbage_collection":
            # Force garbage collection
            collected = gc.collect()
            print(f"🔧 Garbage collection freed {collected} objects")
        
        else:
            print(f"❌ Unknown component: {component}")
    
    def _shutdown_components(self):
        """Shutdown all optimized components"""
        try:
            if self.thread_pool:
                shutdown_global_thread_pool()
                self.thread_pool = None
            
            if self.config_cache:
                shutdown_config_cache()
                self.config_cache = None
            
            if self.message_router:
                shutdown_message_router()
                self.message_router = None
            
            if self.audio_processor:
                shutdown_audio_processor()
                self.audio_processor = None
            
            print("✅ All performance components shutdown")
            
        except Exception as e:
            print(f"❌ Error shutting down performance components: {e}")
    
    def shutdown(self):
        """Shutdown the performance manager"""
        # Stop monitoring
        self.stop_monitoring.set()
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2.0)
        
        # Shutdown components
        self._shutdown_components()
        
        # Clear callbacks and history
        self.performance_callbacks.clear()
        self.metrics_history.clear()
        
        print("🛑 Performance manager shutdown complete")

# Global performance manager instance
_global_performance_manager = None

def get_performance_manager() -> PerformanceManager:
    """Get the global performance manager instance"""
    global _global_performance_manager
    if _global_performance_manager is None:
        _global_performance_manager = PerformanceManager()
    return _global_performance_manager

def shutdown_performance_manager():
    """Shutdown the global performance manager"""
    global _global_performance_manager
    if _global_performance_manager:
        _global_performance_manager.shutdown()
        _global_performance_manager = None

def initialize_performance_optimizations(level: PerformanceLevel = PerformanceLevel.BALANCED):
    """
    Initialize performance optimizations for the application.
    
    Args:
        level: Optimization level to use
    """
    manager = get_performance_manager()
    manager.set_optimization_level(level)
    
    print(f"🚀 Performance optimizations initialized at {level.value} level")
    return manager