"""
High-Performance Configuration Cache - Optimized Config Management

This module implements a high-performance configuration caching system that
eliminates frequent JSON file loading. It provides intelligent caching with
change detection and automatic updates for real-time configuration management.

Key Features:
- Intelligent file change detection using modification timestamps
- Memory-efficient caching with LRU eviction
- Thread-safe access for concurrent operations
- Hot-reload capability for development
- Configuration validation and error handling
- Performance monitoring and statistics

Author: Interaction Framework Team
License: MIT
"""

import json
import os
import time
import threading
import weakref
from typing import Dict, Any, Optional, Callable, Set
from pathlib import Path
from dataclasses import dataclass
from collections import OrderedDict

@dataclass
class CacheEntry:
    """Represents a cached configuration entry"""
    data: Dict[str, Any]
    file_path: str
    last_modified: float
    last_accessed: float
    access_count: int

class ConfigCache:
    """
    High-performance configuration cache with intelligent change detection.
    
    This cache provides fast access to configuration files by keeping them
    in memory and only reloading when the underlying file changes. It uses
    modification timestamps for efficient change detection and LRU eviction
    for memory management.
    """
    
    def __init__(self, max_entries: int = 100, check_interval: float = 1.0):
        """
        Initialize the configuration cache.
        
        Args:
            max_entries: Maximum number of cached entries
            check_interval: Interval in seconds for file change checking
        """
        self.max_entries = max_entries
        self.check_interval = check_interval
        
        # Cache storage with LRU ordering
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.cache_lock = threading.RLock()
        
        # File watching for hot-reload
        self.watched_files: Set[str] = set()
        self.file_watchers: Dict[str, list] = {}
        
        # Performance statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "reloads": 0,
            "errors": 0
        }
        self.stats_lock = threading.Lock()
        
        # Background thread for file monitoring
        self.monitor_thread = threading.Thread(
            target=self._monitor_files,
            name="ConfigCache-Monitor",
            daemon=True
        )
        self.stop_monitoring = threading.Event()
        self.monitor_thread.start()
    
    def get(self, file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get configuration from cache or load from file.
        
        Args:
            file_path: Path to the configuration file
            default: Default value if file doesn't exist or is invalid
            
        Returns:
            Configuration dictionary
        """
        abs_path = os.path.abspath(file_path)
        
        with self.cache_lock:
            # Check if we have a cached entry
            if abs_path in self.cache:
                entry = self.cache[abs_path]
                
                # Check if file has been modified
                if os.path.exists(abs_path):
                    current_mtime = os.path.getmtime(abs_path)
                    
                    if current_mtime <= entry.last_modified:
                        # Cache hit - update access info
                        entry.last_accessed = time.time()
                        entry.access_count += 1
                        self.cache.move_to_end(abs_path)  # LRU update
                        
                        with self.stats_lock:
                            self.stats["hits"] += 1
                        
                        return entry.data.copy()
                    else:
                        # File modified - need to reload
                        self._reload_file(abs_path)
                        return self.cache[abs_path].data.copy()
                else:
                    # File was deleted
                    del self.cache[abs_path]
                    self.watched_files.discard(abs_path)
                    return default or {}
            
            # Cache miss - load from file
            return self._load_file(abs_path, default)
    
    def _load_file(self, file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Load configuration file and add to cache"""
        if not os.path.exists(file_path):
            with self.stats_lock:
                self.stats["misses"] += 1
            return default or {}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Create cache entry
            entry = CacheEntry(
                data=data,
                file_path=file_path,
                last_modified=os.path.getmtime(file_path),
                last_accessed=time.time(),
                access_count=1
            )
            
            # Add to cache with LRU eviction
            self.cache[file_path] = entry
            self.cache.move_to_end(file_path)
            
            # Evict oldest entries if cache is full
            while len(self.cache) > self.max_entries:
                self.cache.popitem(last=False)
            
            # Add to watched files
            self.watched_files.add(file_path)
            
            with self.stats_lock:
                self.stats["misses"] += 1
            
            return data.copy()
            
        except (json.JSONDecodeError, IOError) as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            
            print(f"❌ Error loading config {file_path}: {e}")
            return default or {}
    
    def _reload_file(self, file_path: str):
        """Reload a file that has been modified"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update existing cache entry
            entry = self.cache[file_path]
            entry.data = data
            entry.last_modified = os.path.getmtime(file_path)
            entry.last_accessed = time.time()
            entry.access_count += 1
            
            # Move to end for LRU
            self.cache.move_to_end(file_path)
            
            with self.stats_lock:
                self.stats["reloads"] += 1
            
            # Notify file watchers
            self._notify_watchers(file_path, data)
            
        except (json.JSONDecodeError, IOError) as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            print(f"❌ Error reloading config {file_path}: {e}")
    
    def save(self, file_path: str, data: Dict[str, Any], indent: int = 2):
        """
        Save configuration to file and update cache.
        
        Args:
            file_path: Path to save the configuration
            data: Configuration data to save
            indent: JSON indentation level
        """
        abs_path = os.path.abspath(file_path)
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            
            # Save to file
            with open(abs_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            
            # Update cache
            with self.cache_lock:
                entry = CacheEntry(
                    data=data.copy(),
                    file_path=abs_path,
                    last_modified=os.path.getmtime(abs_path),
                    last_accessed=time.time(),
                    access_count=1
                )
                
                self.cache[abs_path] = entry
                self.cache.move_to_end(abs_path)
                self.watched_files.add(abs_path)
            
            # Notify watchers
            self._notify_watchers(abs_path, data)
            
        except IOError as e:
            with self.stats_lock:
                self.stats["errors"] += 1
            print(f"❌ Error saving config {file_path}: {e}")
            raise
    
    def watch(self, file_path: str, callback: Callable[[str, Dict[str, Any]], None]):
        """
        Register a callback for file changes.
        
        Args:
            file_path: Path to watch
            callback: Function to call when file changes
        """
        abs_path = os.path.abspath(file_path)
        
        if abs_path not in self.file_watchers:
            self.file_watchers[abs_path] = []
        
        self.file_watchers[abs_path].append(callback)
        self.watched_files.add(abs_path)
    
    def _notify_watchers(self, file_path: str, data: Dict[str, Any]):
        """Notify all watchers of a file change"""
        if file_path in self.file_watchers:
            for callback in self.file_watchers[file_path]:
                try:
                    callback(file_path, data)
                except Exception as e:
                    print(f"❌ Error in config watcher callback: {e}")
    
    def _monitor_files(self):
        """Background thread to monitor file changes"""
        while not self.stop_monitoring.is_set():
            try:
                with self.cache_lock:
                    files_to_check = list(self.watched_files)
                
                for file_path in files_to_check:
                    if file_path in self.cache:
                        if os.path.exists(file_path):
                            current_mtime = os.path.getmtime(file_path)
                            cached_mtime = self.cache[file_path].last_modified
                            
                            if current_mtime > cached_mtime:
                                self._reload_file(file_path)
                        else:
                            # File was deleted
                            with self.cache_lock:
                                if file_path in self.cache:
                                    del self.cache[file_path]
                                self.watched_files.discard(file_path)
                
            except Exception as e:
                print(f"❌ Error in file monitoring: {e}")
            
            self.stop_monitoring.wait(self.check_interval)
    
    def invalidate(self, file_path: str):
        """Invalidate a specific cache entry"""
        abs_path = os.path.abspath(file_path)
        
        with self.cache_lock:
            if abs_path in self.cache:
                del self.cache[abs_path]
            self.watched_files.discard(abs_path)
    
    def clear(self):
        """Clear all cache entries"""
        with self.cache_lock:
            self.cache.clear()
            self.watched_files.clear()
            self.file_watchers.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        with self.stats_lock:
            total_requests = self.stats["hits"] + self.stats["misses"]
            hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_size": len(self.cache),
                "hit_rate": hit_rate,
                "total_requests": total_requests,
                "watched_files": len(self.watched_files),
                **self.stats
            }
    
    def shutdown(self):
        """Shutdown the cache and monitoring thread"""
        self.stop_monitoring.set()
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        
        self.clear()
        print("🛑 Configuration cache shutdown complete")

# Global configuration cache instance
_global_config_cache = None

def get_config_cache() -> ConfigCache:
    """Get the global configuration cache instance"""
    global _global_config_cache
    if _global_config_cache is None:
        _global_config_cache = ConfigCache()
    return _global_config_cache

def get_config(file_path: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Convenient function to get configuration using the global cache.
    
    Args:
        file_path: Path to the configuration file
        default: Default value if file doesn't exist
        
    Returns:
        Configuration dictionary
    """
    return get_config_cache().get(file_path, default)

def save_config(file_path: str, data: Dict[str, Any], indent: int = 2):
    """
    Convenient function to save configuration using the global cache.
    
    Args:
        file_path: Path to save the configuration
        data: Configuration data to save
        indent: JSON indentation level
    """
    get_config_cache().save(file_path, data, indent)

def watch_config(file_path: str, callback: Callable[[str, Dict[str, Any]], None]):
    """
    Convenient function to watch configuration changes using the global cache.
    
    Args:
        file_path: Path to watch
        callback: Function to call when file changes
    """
    get_config_cache().watch(file_path, callback)

def shutdown_config_cache():
    """Shutdown the global configuration cache"""
    global _global_config_cache
    if _global_config_cache:
        _global_config_cache.shutdown()
        _global_config_cache = None