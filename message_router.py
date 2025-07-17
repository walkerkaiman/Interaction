"""
Message Router - Event Routing System for Interaction Modules

This file implements the message routing system that connects input modules to
output modules in the Interaction framework. The message router acts as the
central nervous system of the application, handling all communication between
modules.

Key Responsibilities:
1. Connect input modules to output modules
2. Route events from input modules to output modules
3. Manage module lifecycle and cleanup
4. Provide event filtering and transformation
5. Handle error recovery and logging

The message router uses a simple callback-based system where:
- Input modules register event callbacks with output modules
- When an input module emits an event, the router calls all registered callbacks
- Output modules receive events through their handle_event method
- The router manages the connection lifecycle and cleanup

Author: Interaction Framework Team
License: MIT
"""

import os
import sys
import json
import threading
import time
import weakref
from typing import Dict, List, Any, Optional, Callable, Set
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import concurrent.futures
import hashlib
from utils.thread_pool_utils import get_thread_pool, TaskPriority

# High-Performance Event Routing - Integrated from performance package
class EventPriority(Enum):
    """Event priority levels for routing"""
    CRITICAL = 0    # Real-time audio/video triggers
    HIGH = 1        # User interactions
    NORMAL = 2      # Background events
    LOW = 3         # Logging, statistics

@dataclass
class Event:
    """Represents an event in the routing system"""
    data: Dict[str, Any]
    priority: EventPriority
    timestamp: float
    source_module_id: int
    event_id: str = ""

class OptimizedMessageRouter:
    """
    High-performance message router optimized for real-time systems.
    
    This router provides significant performance improvements over the original
    by using lock-free data structures, batched processing, and intelligent
    connection management. It maintains sub-10ms latency for critical events.
    """
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 0.001):
        """
        Initialize the optimized message router.
        
        Args:
            batch_size: Maximum events to process in a single batch
            flush_interval: Maximum time to wait before flushing batched events
        """
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Connection registry using weak references to prevent memory leaks
        self.connections: Dict[int, List[weakref.ref]] = defaultdict(list)
        self.connection_cache: Dict[int, List[Any]] = {}
        self.cache_valid = False
        
        # Event queues for batched processing
        self.event_queues = {
            EventPriority.CRITICAL: deque(),
            EventPriority.HIGH: deque(),
            EventPriority.NORMAL: deque(),
            EventPriority.LOW: deque()
        }
        
        # Minimal locking - only for connection management
        self.connection_lock = threading.RLock()
        
        # Performance statistics
        self.stats = {
            "events_routed": 0,
            "events_dropped": 0,
            "avg_latency": 0.0,
            "connections_active": 0,
            "batch_processing_time": 0.0
        }
        self.stats_lock = threading.Lock()
        
        # Background processing
        self.thread_pool = get_thread_pool()
        self.shutdown_event = threading.Event()
        
        # Start batch processor
        self.batch_processor = threading.Thread(
            target=self._batch_processor,
            name="MessageRouter-BatchProcessor",
            daemon=True
        )
        self.batch_processor.start()
    
    def connect_modules(self, input_module, output_module) -> bool:
        """
        Connect an input module to an output module.
        
        Args:
            input_module: The input module that will emit events
            output_module: The output module that will receive events
            
        Returns:
            bool: True if connection was successful
        """
        # Validate module compatibility
        if not self._validate_module_compatibility(input_module, output_module):
            return False
        
        input_id = id(input_module)
        
        with self.connection_lock:
            # Use weak references to prevent memory leaks
            output_ref = weakref.ref(output_module, self._cleanup_dead_reference)
            
            # Add to connections if not already present
            if output_ref not in self.connections[input_id]:
                self.connections[input_id].append(output_ref)
                self.cache_valid = False
                
                # Set up event callback for immediate routing
                if hasattr(input_module, 'add_event_callback'):
                    input_module.add_event_callback(
                        lambda event: self._route_event_immediate(input_id, event)
                    )
                
                with self.stats_lock:
                    self.stats["connections_active"] += 1
                
                return True
        
        return False
    
    def disconnect_modules(self, input_module, output_module) -> bool:
        """
        Disconnect an input module from an output module.
        
        Args:
            input_module: The input module
            output_module: The output module
            
        Returns:
            bool: True if disconnection was successful
        """
        input_id = id(input_module)
        
        with self.connection_lock:
            if input_id in self.connections:
                # Find and remove the connection
                connections = self.connections[input_id]
                for i, ref in enumerate(connections):
                    if ref() is output_module:
                        del connections[i]
                        self.cache_valid = False
                        
                        # Remove callback if possible
                        if hasattr(input_module, 'remove_event_callback'):
                            input_module.remove_event_callback(output_module.handle_event)
                        
                        with self.stats_lock:
                            self.stats["connections_active"] -= 1
                        
                        return True
        
        return False
    
    def _validate_module_compatibility(self, input_module, output_module) -> bool:
        """Validate that modules are compatible for connection"""
        # Check if modules have required methods
        if not hasattr(output_module, 'handle_event'):
            return False
        
        # Check classification compatibility
        input_classification = getattr(input_module, 'manifest', {}).get('classification', 'unknown')
        output_classification = getattr(output_module, 'manifest', {}).get('classification', 'unknown')
        
        # Define compatible combinations
        compatible_combinations = {
            'trigger': ['trigger', 'streaming'],
            'streaming': ['streaming', 'trigger'],
        }
        
        if input_classification in compatible_combinations:
            return output_classification in compatible_combinations[input_classification]
        
        return True  # Default to compatible if unknown
    
    def _route_event_immediate(self, input_id: int, event_data: Dict[str, Any]):
        """
        Route an event immediately for critical real-time processing.
        
        Args:
            input_id: ID of the input module
            event_data: Event data to route
        """
        # Determine event priority
        priority = self._determine_event_priority(event_data)
        
        # Create event object
        event = Event(
            data=event_data,
            priority=priority,
            timestamp=time.time(),
            source_module_id=input_id
        )
        
        # For critical events, route immediately
        if priority == EventPriority.CRITICAL:
            self._route_event_direct(input_id, event)
        else:
            # Queue for batched processing
            self.event_queues[priority].append(event)
    
    def _route_event_direct(self, input_id: int, event: Event):
        """
        Route an event directly to all connected modules.
        
        Args:
            input_id: ID of the input module
            event: Event to route
        """
        start_time = time.time()
        
        # Get cached connections for performance
        connections = self._get_cached_connections(input_id)
        
        # Route to all connected modules
        for output_module in connections:
            try:
                if hasattr(output_module, 'handle_event'):
                    output_module.handle_event(event.data)
            except Exception as e:
                print(f"❌ Error routing event to module: {e}")
        
        # Update statistics
        processing_time = time.time() - start_time
        with self.stats_lock:
            self.stats["events_routed"] += 1
            self.stats["avg_latency"] = (
                (self.stats["avg_latency"] * (self.stats["events_routed"] - 1) + processing_time) 
                / self.stats["events_routed"]
            )
    
    def _batch_processor(self):
        """Background thread for processing batched events"""
        while not self.shutdown_event.is_set():
            try:
                # Process events in priority order
                for priority in EventPriority:
                    if self.event_queues[priority]:
                        self._process_batched_events(priority)
                
                # Small delay to prevent busy waiting
                time.sleep(self.flush_interval)
                
            except Exception as e:
                print(f"❌ Error in batch processor: {e}")
    
    def _process_batched_events(self, priority: EventPriority):
        """Process a batch of events for a given priority"""
        queue = self.event_queues[priority]
        if not queue:
            return
        
        # Collect events for batch processing
        events = []
        while queue and len(events) < self.batch_size:
            events.append(queue.popleft())
        
        if events:
            # Process batch in thread pool for non-blocking operation
            self.thread_pool.submit(
                self._process_event_batch,
                events,
                priority=TaskPriority.HIGH if priority in [EventPriority.CRITICAL, EventPriority.HIGH] else TaskPriority.NORMAL
            )
    
    def _process_event_batch(self, events: List[Event]):
        """Process a batch of events"""
        start_time = time.time()
        
        # Group events by source module for efficient routing
        events_by_source = defaultdict(list)
        for event in events:
            events_by_source[event.source_module_id].append(event)
        
        # Process each source's events
        for source_id, source_events in events_by_source.items():
            connections = self._get_cached_connections(source_id)
            
            for event in source_events:
                for output_module in connections:
                    try:
                        if hasattr(output_module, 'handle_event'):
                            output_module.handle_event(event.data)
                    except Exception as e:
                        print(f"❌ Error processing batched event: {e}")
        
        # Update statistics
        processing_time = time.time() - start_time
        with self.stats_lock:
            self.stats["events_routed"] += len(events)
            self.stats["batch_processing_time"] = processing_time
    
    def _get_cached_connections(self, input_id: int) -> List[Any]:
        """Get cached connections for an input module"""
        if not self.cache_valid:
            self._rebuild_connection_cache()
        
        return self.connection_cache.get(input_id, [])
    
    def _rebuild_connection_cache(self):
        """Rebuild the connection cache from weak references"""
        with self.connection_lock:
            self.connection_cache.clear()
            
            for input_id, refs in self.connections.items():
                valid_connections = []
                for ref in refs:
                    module = ref()
                    if module is not None:
                        valid_connections.append(module)
                    else:
                        # Clean up dead references
                        self.connections[input_id].remove(ref)
                
                if valid_connections:
                    self.connection_cache[input_id] = valid_connections
                elif not self.connections[input_id]:
                    # Remove empty connection lists
                    del self.connections[input_id]
            
            self.cache_valid = True
    
    def _determine_event_priority(self, event_data: Dict[str, Any]) -> EventPriority:
        """Determine the priority of an event based on its data"""
        # Check for critical event types
        if event_data.get('type') in ['audio_trigger', 'osc_trigger', 'dmx_trigger']:
            return EventPriority.CRITICAL
        
        # Check for high-priority user interactions
        if event_data.get('type') in ['user_input', 'button_press', 'touch']:
            return EventPriority.HIGH
        
        # Check for low-priority logging events
        if event_data.get('type') in ['log', 'debug', 'statistics']:
            return EventPriority.LOW
        
        # Default to normal priority
        return EventPriority.NORMAL
    
    def _cleanup_dead_reference(self, ref):
        """Clean up dead weak references"""
        self.cache_valid = False
        with self.stats_lock:
            self.stats["connections_active"] = max(0, self.stats["connections_active"] - 1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        with self.stats_lock:
            return {
                "events_routed": self.stats["events_routed"],
                "events_dropped": self.stats["events_dropped"],
                "avg_latency_ms": self.stats["avg_latency"] * 1000,
                "connections_active": self.stats["connections_active"],
                "batch_processing_time_ms": self.stats["batch_processing_time"] * 1000,
                "queue_sizes": {p.name: len(q) for p, q in self.event_queues.items()}
            }
    
    def clear_all_connections(self):
        """Clear all module connections"""
        with self.connection_lock:
            self.connections.clear()
            self.connection_cache.clear()
            self.cache_valid = True
            
            with self.stats_lock:
                self.stats["connections_active"] = 0
    
    def shutdown(self):
        """Shutdown the message router"""
        self.shutdown_event.set()
        if self.batch_processor.is_alive():
            self.batch_processor.join(timeout=2.0)
        print("🛑 Optimized message router shutdown complete")

# Global optimized message router instance
_global_optimized_router = None

def get_message_router() -> OptimizedMessageRouter:
    """Get the global optimized message router instance"""
    global _global_optimized_router
    if _global_optimized_router is None:
        _global_optimized_router = OptimizedMessageRouter()
    return _global_optimized_router

def shutdown_message_router():
    """Shutdown the global optimized message router"""
    global _global_optimized_router
    if _global_optimized_router:
        _global_optimized_router.shutdown()
        _global_optimized_router = None

class EventRouter:
    """
    Central event routing system for modules, GUI, and system events.
    Supports state tracking, settings-based routing, event subscription/publication,
    runtime reconfiguration, and debugging/logging hooks.
    """
    def __init__(self):
        self.connections = {}  # {input_settings_key: [output_modules]}
        self.state_subscribers = []  # [(module, callback)]
        self.event_subscribers = {}  # {event_type: [(callback, filter)]}
        self.lock = threading.Lock()
        self.module_states = {}  # {module_id: state}
        self.debug_log = []  # [(event_type, data, meta)]

    def _settings_key(self, settings: dict) -> str:
        # Create a hashable key from settings dict for grouping
        return hashlib.sha256(str(sorted(settings.items())).encode()).hexdigest() if settings else "default"

    def connect_modules(self, input_module, output_module, settings: Optional[dict]=None):
        # Use settings key for grouping outputs by input settings
        key = self._settings_key(settings or getattr(input_module, 'config', {}))
        with self.lock:
            if key not in self.connections:
                self.connections[key] = []
            if output_module not in self.connections[key]:
                self.connections[key].append(output_module)
                input_module.add_event_callback(output_module.handle_event)
                self._log_debug('connect', {'input': input_module, 'output': output_module, 'settings': settings})
        return True

    def disconnect_modules(self, input_module, output_module, settings: Optional[dict]=None):
        key = self._settings_key(settings or getattr(input_module, 'config', {}))
        with self.lock:
            if key in self.connections and output_module in self.connections[key]:
                self.connections[key].remove(output_module)
                input_module.remove_event_callback(output_module.handle_event)
                self._log_debug('disconnect', {'input': input_module, 'output': output_module, 'settings': settings})
                if not self.connections[key]:
                    del self.connections[key]

    def subscribe(self, event_type: str, callback: Callable, filter: Optional[Callable]=None):
        with self.lock:
            if event_type not in self.event_subscribers:
                self.event_subscribers[event_type] = []
            self.event_subscribers[event_type].append((callback, filter))

    def unsubscribe(self, event_type: str, callback: Callable):
        with self.lock:
            if event_type in self.event_subscribers:
                self.event_subscribers[event_type] = [
                    (cb, f) for (cb, f) in self.event_subscribers[event_type] if cb != callback
                ]

    def publish(self, event_type: str, data: Any, settings: Optional[dict]=None):
        # Publish an event to all subscribers (optionally filtered by settings)
        with self.lock:
            for cb, filt in self.event_subscribers.get(event_type, []):
                if filt is None or filt(data, settings):
                    cb(data)
            self._log_debug('publish', {'event_type': event_type, 'data': data, 'settings': settings})

    def register_state_subscriber(self, module, callback: Callable):
        with self.lock:
            self.state_subscribers.append((module, callback))

    def emit_state_change(self, module, new_state: str):
        module_id = id(module)
        with self.lock:
            self.module_states[module_id] = new_state
            for m, cb in self.state_subscribers:
                if m is None or m == module:
                    cb(module, new_state)
            self._log_debug('state_change', {'module': module, 'state': new_state})

    def get_module_state(self, module) -> Optional[str]:
        return self.module_states.get(id(module))

    def get_all_states(self) -> Dict[int, str]:
        return dict(self.module_states)

    def get_connections(self):
        with self.lock:
            return {k: list(v) for k, v in self.connections.items()}

    def reconfigure_connection(self, input_module, output_module, old_settings: dict, new_settings: dict):
        self.disconnect_modules(input_module, output_module, old_settings)
        self.connect_modules(input_module, output_module, new_settings)
        self._log_debug('reconfigure', {'input': input_module, 'output': output_module, 'old': old_settings, 'new': new_settings})

    def clear_all_connections(self):
        with self.lock:
            for key, outputs in self.connections.items():
                for output in outputs:
                    # No direct reference to input_module, so this is a best-effort cleanup
                    pass
            self.connections.clear()
            self._log_debug('clear_all', {})

    def _log_debug(self, event_type, meta):
        self.debug_log.append((event_type, meta))
        # Optionally, print or send to GUI for live debugging

# For backward compatibility
MessageRouter = EventRouter
