"""
Performance Package - High-Performance Optimizations for Interactive Art Framework

This package provides comprehensive performance optimizations for the Interactive
Art Installation Framework, including thread pooling, configuration caching,
message routing, and audio processing optimizations.

Key Components:
- PerformanceManager: Unified performance coordination
- OptimizedThreadPool: High-performance thread management
- ConfigCache: Intelligent configuration caching
- OptimizedMessageRouter: Low-latency event routing
- OptimizedAudioProcessor: Vectorized audio processing

Usage:
    from performance import initialize_performance_optimizations, PerformanceLevel
    
    # Initialize optimizations
    manager = initialize_performance_optimizations(PerformanceLevel.BALANCED)
    
    # Get performance status
    status = manager.get_performance_summary()
    
    # Shutdown when done
    manager.shutdown()

Author: Interaction Framework Team
License: MIT
"""

# Import main components
from .performance_manager import (
    PerformanceManager,
    PerformanceLevel,
    PerformanceMetrics,
    get_performance_manager,
    shutdown_performance_manager,
    initialize_performance_optimizations
)

from .thread_pool import (
    OptimizedThreadPool,
    TaskPriority,
    get_thread_pool,
    shutdown_global_thread_pool
)

from .config_cache import (
    ConfigCache,
    get_config_cache,
    get_config,
    save_config,
    watch_config,
    shutdown_config_cache
)

from .optimized_message_router import (
    OptimizedMessageRouter,
    EventPriority,
    get_message_router,
    shutdown_message_router
)

from .optimized_audio_processing import (
    OptimizedAudioProcessor,
    get_audio_processor,
    generate_waveform_optimized,
    shutdown_audio_processor
)

__all__ = [
    # Performance Manager
    'PerformanceManager',
    'PerformanceLevel',
    'PerformanceMetrics',
    'get_performance_manager',
    'shutdown_performance_manager',
    'initialize_performance_optimizations',
    
    # Thread Pool
    'OptimizedThreadPool',
    'TaskPriority',
    'get_thread_pool',
    'shutdown_global_thread_pool',
    
    # Config Cache
    'ConfigCache',
    'get_config_cache',
    'get_config',
    'save_config',
    'watch_config',
    'shutdown_config_cache',
    
    # Message Router
    'OptimizedMessageRouter',
    'EventPriority',
    'get_message_router',
    'shutdown_message_router',
    
    # Audio Processing
    'OptimizedAudioProcessor',
    'get_audio_processor',
    'generate_waveform_optimized',
    'shutdown_audio_processor'
]

# Version info
__version__ = "1.0.0"
__author__ = "Interaction Framework Team"