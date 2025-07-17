"""
Thread Pool Utilities - Shared thread pool implementation

This file provides the thread pool functionality that was previously
integrated into module_loader.py to avoid circular import dependencies.
"""

import threading
import queue
import time
import concurrent.futures
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class TaskPriority(Enum):
    """Task priority levels for real-time processing"""
    CRITICAL = 0    # Real-time events (OSC, audio triggers)
    HIGH = 1        # User interface updates
    NORMAL = 2      # Background processing
    LOW = 3         # Cleanup, maintenance tasks

@dataclass
class Task:
    """Represents a task in the thread pool"""
    func: Callable
    args: tuple
    kwargs: dict
    priority: TaskPriority
    timestamp: float
    future: Optional[concurrent.futures.Future] = None

class OptimizedThreadPool:
    """
    High-performance thread pool optimized for real-time applications.
    
    This thread pool is specifically designed for interactive art installations
    where low latency and predictable performance are critical. It provides:
    
    - Priority-based task scheduling
    - Pre-allocated worker threads
    - Automatic scaling based on load
    - Memory-efficient task queuing
    - Real-time performance monitoring
    """
    
    def __init__(self, min_threads: int = 2, max_threads: int = 8, 
                 thread_name_prefix: str = "InteractionWorker"):
        """
        Initialize the optimized thread pool.
        
        Args:
            min_threads: Minimum number of threads to maintain
            max_threads: Maximum number of threads to create
            thread_name_prefix: Prefix for thread names
        """
        self.min_threads = min_threads
        self.max_threads = max_threads
        self.thread_name_prefix = thread_name_prefix
        
        # Priority queues for different task types
        self.task_queues = {
            TaskPriority.CRITICAL: queue.Queue(),
            TaskPriority.HIGH: queue.Queue(),
            TaskPriority.NORMAL: queue.Queue(),
            TaskPriority.LOW: queue.Queue()
        }
        
        # Worker thread management
        self.workers = []
        self.worker_lock = threading.Lock()
        self.shutdown_event = threading.Event()
        
        # Performance monitoring
        self.tasks_processed = 0
        self.total_processing_time = 0.0
        self.active_tasks = 0
        self.stats_lock = threading.Lock()
        
        # Initialize core worker threads
        self._create_workers(min_threads)
        
        # Start monitoring thread for automatic scaling
        self.monitor_thread = threading.Thread(
            target=self._monitor_performance,
            name=f"{thread_name_prefix}-Monitor",
            daemon=True
        )
        self.monitor_thread.start()
    
    def _create_workers(self, count: int):
        """Create worker threads"""
        with self.worker_lock:
            for i in range(count):
                worker = threading.Thread(
                    target=self._worker_loop,
                    name=f"{self.thread_name_prefix}-{len(self.workers) + 1}",
                    daemon=True
                )
                worker.start()
                self.workers.append(worker)
    
    def _worker_loop(self):
        """Main worker thread loop with priority-based task processing"""
        while not self.shutdown_event.is_set():
            task = self._get_next_task()
            if task is None:
                continue
                
            # Execute task with performance monitoring
            start_time = time.time()
            try:
                with self.stats_lock:
                    self.active_tasks += 1
                
                result = task.func(*task.args, **task.kwargs)
                
                if task.future:
                    try:
                        task.future.set_result(result)
                    except concurrent.futures.InvalidStateError:
                        # The future was cancelled, ignore this error
                        pass
                    
            except Exception as e:
                if task.future:
                    try:
                        task.future.set_exception(e)
                    except concurrent.futures.InvalidStateError:
                        # The future was cancelled, ignore this error
                        pass
                # Log error but continue processing
                print(f"❌ Task execution error: {e}")
            finally:
                processing_time = time.time() - start_time
                with self.stats_lock:
                    self.active_tasks -= 1
                    self.tasks_processed += 1
                    self.total_processing_time += processing_time
    
    def _get_next_task(self) -> Optional[Task]:
        """Get the next task based on priority"""
        # Check queues in priority order
        for priority in TaskPriority:
            try:
                task = self.task_queues[priority].get_nowait()
                return task
            except queue.Empty:
                continue
        
        # If no tasks available, wait on critical queue with timeout
        try:
            task = self.task_queues[TaskPriority.CRITICAL].get(timeout=0.1)
            return task
        except queue.Empty:
            return None
    
    def submit(self, func: Callable, *args, priority: TaskPriority = TaskPriority.NORMAL, 
               **kwargs) -> concurrent.futures.Future:
        """
        Submit a task to the thread pool.
        
        Args:
            func: Function to execute
            *args: Arguments for the function
            priority: Task priority level
            **kwargs: Keyword arguments for the function
            
        Returns:
            Future object for the task result
        """
        if self.shutdown_event.is_set():
            raise RuntimeError("Thread pool is shut down")
        
        future = concurrent.futures.Future()
        task = Task(
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timestamp=time.time(),
            future=future
        )
        
        self.task_queues[priority].put(task)
        return future
    
    def submit_realtime(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit a real-time critical task"""
        return self.submit(func, *args, priority=TaskPriority.CRITICAL, **kwargs)
    
    def submit_ui(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """Submit a UI update task"""
        return self.submit(func, *args, priority=TaskPriority.HIGH, **kwargs)
    
    def _monitor_performance(self):
        """Monitor thread pool performance and auto-scale"""
        while not self.shutdown_event.is_set():
            try:
                # Check if we need more workers
                with self.stats_lock:
                    avg_processing_time = (self.total_processing_time / max(self.tasks_processed, 1))
                    queue_sizes = {p: q.qsize() for p, q in self.task_queues.items()}
                    total_queued = sum(queue_sizes.values())
                
                # Scale up if needed
                if (total_queued > len(self.workers) * 2 and 
                    len(self.workers) < self.max_threads):
                    self._create_workers(1)
                
                # Scale down if possible
                elif (total_queued < len(self.workers) // 2 and 
                      len(self.workers) > self.min_threads):
                    # Let workers naturally finish and don't create new ones
                    pass
                    
            except Exception as e:
                print(f"❌ Error in thread pool monitoring: {e}")
            
            time.sleep(1.0)  # Check every second
    
    def get_stats(self) -> Dict[str, Any]:
        """Get thread pool statistics"""
        with self.stats_lock:
            avg_processing_time = (self.total_processing_time / max(self.tasks_processed, 1))
            queue_sizes = {p.name: q.qsize() for p, q in self.task_queues.items()}
            
            return {
                "active_workers": len(self.workers),
                "active_tasks": self.active_tasks,
                "tasks_processed": self.tasks_processed,
                "avg_processing_time": avg_processing_time,
                "queue_sizes": queue_sizes,
                "shutdown": self.shutdown_event.is_set()
            }
    
    def shutdown(self, wait: bool = True):
        """Shutdown the thread pool"""
        self.shutdown_event.set()
        if wait:
            for worker in self.workers:
                worker.join(timeout=5.0)

# Global thread pool instance
_global_thread_pool: Optional[OptimizedThreadPool] = None

def get_thread_pool() -> OptimizedThreadPool:
    """Get the global thread pool instance"""
    global _global_thread_pool
    if _global_thread_pool is None:
        _global_thread_pool = OptimizedThreadPool()
    return _global_thread_pool

def shutdown_global_thread_pool():
    """Shutdown the global thread pool"""
    global _global_thread_pool
    if _global_thread_pool:
        _global_thread_pool.shutdown()
        _global_thread_pool = None 