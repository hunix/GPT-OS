#!/usr/bin/env python3
"""
GPT-OS Enterprise v2.0: Production-Grade AI-Powered Natural Language Shell
Enterprise architecture with async operations, resilience patterns, and observability
"""

import os
import sys
import asyncio
import subprocess
import json
import re
import time
import logging
import hashlib
from typing import Optional, Tuple, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import OrderedDict, deque
from functools import wraps
import random

# Third-party imports
from openai import AsyncOpenAI
import gc as python_gc

# Local imports
from input_validator import InputValidator, ValidationResult

# ============================================================================
# CONSTANTS
# ============================================================================

# Metrics constants
MAX_HISTOGRAM_SIZE = 1000
MAX_OUTPUT_LINES_DEFAULT = 1000

# Cache constants
DEFAULT_CACHE_SIZE = 1000
DEFAULT_CACHE_TTL = 3600  # 1 hour in seconds

# Circuit Breaker constants
DEFAULT_FAILURE_THRESHOLD = 5
DEFAULT_RECOVERY_TIMEOUT = 60  # seconds
DEFAULT_SUCCESS_THRESHOLD = 2

# Retry constants
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 10.0  # seconds

# Rate Limiting constants
DEFAULT_REQUESTS_PER_MINUTE = 60
DEFAULT_BURST_SIZE = 10

# Task Queue constants
DEFAULT_WORKERS = 4
DEFAULT_QUEUE_SIZE = 100

# Memory Management constants
DEFAULT_MAX_HISTORY = 1000
DEFAULT_GC_INTERVAL = 300  # 5 minutes in seconds

# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

@dataclass
class Config:
    """Centralized configuration management"""
    # LLM Configuration
    llm_provider: str = "openai"
    llm_model: str = "gpt-4.1-mini"
    llm_timeout: int = 10
    llm_max_tokens: int = 500
    llm_temperature: float = 0.3
    
    # Fallback Models
    fallback_models: List[str] = field(default_factory=lambda: ["gpt-4.1-nano", "gemini-2.5-flash"])
    
    # Circuit Breaker
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = DEFAULT_FAILURE_THRESHOLD
    circuit_breaker_recovery_timeout: int = DEFAULT_RECOVERY_TIMEOUT
    circuit_breaker_success_threshold: int = DEFAULT_SUCCESS_THRESHOLD
    
    # Retry Configuration
    retry_max_attempts: int = DEFAULT_MAX_ATTEMPTS
    retry_base_delay: float = DEFAULT_BASE_DELAY
    retry_max_delay: float = DEFAULT_MAX_DELAY
    retry_exponential_base: int = 2
    retry_jitter: bool = True
    
    # Cache Configuration
    cache_enabled: bool = True
    cache_max_size: int = DEFAULT_CACHE_SIZE
    cache_ttl: int = DEFAULT_CACHE_TTL
    
    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_requests_per_minute: int = DEFAULT_REQUESTS_PER_MINUTE
    rate_limit_burst_size: int = DEFAULT_BURST_SIZE
    
    # Task Queue
    task_queue_workers: int = DEFAULT_WORKERS
    task_queue_max_size: int = DEFAULT_QUEUE_SIZE
    task_queue_timeout: int = 300
    
    # Memory Management
    memory_max_history: int = DEFAULT_MAX_HISTORY
    memory_gc_interval: int = DEFAULT_GC_INTERVAL
    memory_cache_max_mb: int = 100
    
    # Command Execution
    command_timeout: int = 30
    command_max_output_lines: int = MAX_OUTPUT_LINES_DEFAULT
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Health Checks
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> 'Config':
        """Load configuration from environment variables"""
        config = cls()
        
        # Override from environment
        if os.getenv('GPTOS_LLM_MODEL'):
            config.llm_model = os.getenv('GPTOS_LLM_MODEL')
        if os.getenv('GPTOS_LOG_LEVEL'):
            config.log_level = os.getenv('GPTOS_LOG_LEVEL')
        if os.getenv('GPTOS_CACHE_ENABLED'):
            config.cache_enabled = os.getenv('GPTOS_CACHE_ENABLED').lower() == 'true'
            
        return config


# ============================================================================
# STRUCTURED LOGGING
# ============================================================================

class StructuredLogger:
    """JSON-based structured logging"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level))
        
        # JSON formatter - avoid duplicate handlers
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(handler)
        
    def _log(self, level: str, event: str, **kwargs: Any) -> None:
        """Log structured message"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "event": event,
            **kwargs
        }
        
        if level == "DEBUG":
            self.logger.debug(json.dumps(log_entry))
        elif level == "INFO":
            self.logger.info(json.dumps(log_entry))
        elif level == "WARNING":
            self.logger.warning(json.dumps(log_entry))
        elif level == "ERROR":
            self.logger.error(json.dumps(log_entry))
        elif level == "CRITICAL":
            self.logger.critical(json.dumps(log_entry))
    
    def debug(self, event: str, **kwargs: Any) -> None:
        """Log debug message"""
        self._log("DEBUG", event, **kwargs)
    
    def info(self, event: str, **kwargs: Any) -> None:
        """Log info message"""
        self._log("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs: Any) -> None:
        """Log warning message"""
        self._log("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs: Any) -> None:
        """Log error message"""
        self._log("ERROR", event, **kwargs)
    
    def critical(self, event: str, **kwargs: Any) -> None:
        """Log critical message"""
        self._log("CRITICAL", event, **kwargs)


# ============================================================================
# METRICS COLLECTION
# ============================================================================

class Metrics:
    """In-memory metrics collection"""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = {}
        
    def increment(self, name: str, value: int = 1) -> None:
        """Increment counter by value"""
        self.counters[name] = self.counters.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float) -> None:
        """Set gauge to specific value"""
        self.gauges[name] = value
    
    def observe(self, name: str, value: float) -> None:
        """Record histogram observation for latency/duration metrics"""
        if name not in self.histograms:
            self.histograms[name] = []
        self.histograms[name].append(value)
        
        # Keep only last MAX_HISTOGRAM_SIZE observations
        if len(self.histograms[name]) > MAX_HISTOGRAM_SIZE:
            self.histograms[name] = self.histograms[name][-MAX_HISTOGRAM_SIZE:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get all metrics"""
        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0
                }
                for name, values in self.histograms.items()
            }
        }


# ============================================================================
# CIRCUIT BREAKER PATTERN
# ============================================================================

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, config: Config, logger: StructuredLogger, metrics: Metrics):
        self.config = config
        self.logger = logger
        self.metrics = metrics
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_state_change: datetime = datetime.now()
        
    def should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if not self.config.circuit_breaker_enabled:
            return True
        
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.config.circuit_breaker_recovery_timeout:
                    self._transition_to_half_open()
                    return True
            return False
        
        if self.state == CircuitState.HALF_OPEN:
            return True
        
        return False
    
    def record_success(self):
        """Record successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.circuit_breaker_success_threshold:
                self._transition_to_closed()
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def record_failure(self):
        """Record failed request"""
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self._transition_to_open()
        elif self.state == CircuitState.CLOSED:
            self.failure_count += 1
            if self.failure_count >= self.config.circuit_breaker_failure_threshold:
                self._transition_to_open()
    
    def _transition_to_open(self):
        """Transition to OPEN state"""
        self.state = CircuitState.OPEN
        self.last_state_change = datetime.now()
        self.logger.warning("circuit_breaker_opened", 
                          failure_count=self.failure_count)
        self.metrics.set_gauge("circuit_breaker_state", 1)  # OPEN
    
    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.last_state_change = datetime.now()
        self.logger.info("circuit_breaker_half_opened")
        self.metrics.set_gauge("circuit_breaker_state", 0.5)  # HALF_OPEN
    
    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_state_change = datetime.now()
        self.logger.info("circuit_breaker_closed")
        self.metrics.set_gauge("circuit_breaker_state", 0)  # CLOSED


# ============================================================================
# CACHING LAYER
# ============================================================================

@dataclass
class CacheEntry:
    """Cache entry with TTL"""
    value: Any
    timestamp: datetime
    ttl: int
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed >= self.ttl


class LRUCache:
    """LRU cache with TTL support"""
    
    def __init__(self, config: Config, logger: StructuredLogger, metrics: Metrics):
        self.config = config
        self.logger = logger
        self.metrics = metrics
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.config.cache_enabled:
            return None
        
        if key not in self.cache:
            self.metrics.increment("cache_miss")
            return None
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired():
            del self.cache[key]
            self.metrics.increment("cache_expired")
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(key)
        self.metrics.increment("cache_hit")
        
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache"""
        if not self.config.cache_enabled:
            return
        
        if ttl is None:
            ttl = self.config.cache_ttl
        
        # Evict if at capacity
        if len(self.cache) >= self.config.cache_max_size:
            self.cache.popitem(last=False)  # Remove oldest
            self.metrics.increment("cache_eviction")
        
        self.cache[key] = CacheEntry(value, datetime.now(), ttl)
        self.metrics.set_gauge("cache_size", len(self.cache))
    
    def clear(self):
        """Clear all cache entries"""
        self.cache.clear()
        self.metrics.set_gauge("cache_size", 0)
    
    def cleanup_expired(self):
        """Remove expired entries"""
        expired_keys = [k for k, v in self.cache.items() if v.is_expired()]
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            self.logger.debug("cache_cleanup", removed=len(expired_keys))
            self.metrics.set_gauge("cache_size", len(self.cache))


# ============================================================================
# RATE LIMITER
# ============================================================================

class TokenBucket:
    """Token bucket rate limiter"""
    
    def __init__(self, config: Config, logger: StructuredLogger):
        self.config = config
        self.logger = logger
        self.tokens = config.rate_limit_burst_size
        self.last_update = time.time()
        self.rate = config.rate_limit_requests_per_minute / 60.0  # tokens per second
    
    def allow_request(self) -> bool:
        """Check if request is allowed"""
        if not self.config.rate_limit_enabled:
            return True
        
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on elapsed time
        self.tokens = min(
            self.config.rate_limit_burst_size,
            self.tokens + elapsed * self.rate
        )
        self.last_update = now
        
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        
        self.logger.warning("rate_limit_exceeded")
        return False


# ============================================================================
# RETRY WITH EXPONENTIAL BACKOFF
# ============================================================================

def async_retry(config: Config, logger: StructuredLogger, metrics: Metrics):
    """Decorator for async retry with exponential backoff"""
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.retry_max_attempts):
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info("retry_succeeded", attempt=attempt)
                        metrics.increment("retry_success")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    
                    if attempt < config.retry_max_attempts - 1:
                        # Calculate delay with exponential backoff
                        delay = min(
                            config.retry_max_delay,
                            config.retry_base_delay * (config.retry_exponential_base ** attempt)
                        )
                        
                        # Add jitter
                        if config.retry_jitter:
                            delay += random.uniform(0, delay * 0.1)
                        
                        logger.warning("retry_attempt", 
                                     attempt=attempt + 1,
                                     delay=delay,
                                     error=str(e))
                        metrics.increment("retry_attempt")
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error("retry_exhausted", 
                                   attempts=config.retry_max_attempts,
                                   error=str(e))
                        metrics.increment("retry_exhausted")
            
            raise last_exception
        
        return wrapper
    return decorator


# ============================================================================
# MEMORY MANAGEMENT
# ============================================================================

class MemoryManager:
    """Memory management with garbage collection"""
    
    def __init__(self, config: Config, logger: StructuredLogger, metrics: Metrics):
        self.config = config
        self.logger = logger
        self.metrics = metrics
        self.history: deque = deque(maxlen=config.memory_max_history)
        self.last_gc = time.time()
    
    def add_to_history(self, entry: Dict[str, Any]):
        """Add entry to history with automatic size management"""
        self.history.append(entry)
        self.metrics.set_gauge("history_size", len(self.history))
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get history entries"""
        if limit:
            return list(self.history)[-limit:]
        return list(self.history)
    
    def clear_history(self):
        """Clear all history"""
        self.history.clear()
        self.metrics.set_gauge("history_size", 0)
    
    async def periodic_gc(self):
        """Periodic garbage collection"""
        while True:
            await asyncio.sleep(self.config.memory_gc_interval)
            
            # Force Python garbage collection
            collected = python_gc.collect()
            
            self.logger.debug("garbage_collection", 
                            objects_collected=collected,
                            history_size=len(self.history))
            self.metrics.increment("gc_runs")


# ============================================================================
# LLM SERVICE WITH RESILIENCE
# ============================================================================

class LLMService:
    """LLM service with circuit breaker, retry, cache, and fallbacks"""
    
    def __init__(self, config: Config, logger: StructuredLogger, 
                 metrics: Metrics, circuit_breaker: CircuitBreaker,
                 cache: LRUCache, rate_limiter: TokenBucket):
        self.config = config
        self.logger = logger
        self.metrics = metrics
        self.circuit_breaker = circuit_breaker
        self.cache = cache
        self.rate_limiter = rate_limiter
        
        self.client = AsyncOpenAI()
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Build system prompt for LLM"""
        return """You are GPT-OS, an intelligent Linux shell assistant. Your role is to:

1. Translate natural language requests into precise Linux shell commands
2. Provide clear explanations of what the command does
3. Warn about potentially dangerous operations
4. Support multiple languages and accents
5. Be conversational and helpful

When responding, use this JSON format:
{
    "command": "the actual shell command to execute",
    "explanation": "human-friendly explanation of what this does",
    "warning": "warning message if dangerous, otherwise null",
    "safe": true/false
}

Examples:
- "update my software" → {"command": "sudo apt update && sudo apt upgrade -y", "explanation": "This updates your package lists and upgrades all installed packages", "warning": null, "safe": true}
- "delete everything in this folder" → {"command": "rm -rf *", "explanation": "This permanently deletes all files and folders in the current directory", "warning": "⚠️ This is DESTRUCTIVE and cannot be undone!", "safe": false}
- "show me large files" → {"command": "du -ah . | sort -rh | head -20", "explanation": "This shows the 20 largest files and folders in the current directory", "warning": null, "safe": true}

Always respond ONLY with valid JSON. No additional text."""
    
    def _generate_cache_key(self, user_input: str, context: str) -> str:
        """Generate cache key from input"""
        combined = f"{user_input}:{context}"
        return hashlib.md5(combined.encode()).hexdigest()
    
    async def translate_command(self, user_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Translate natural language to command with full resilience"""
        start_time = time.time()
        
        try:
            # Check rate limit
            if not self.rate_limiter.allow_request():
                self.logger.warning("rate_limited", user_input=user_input)
                return None
            
            # Check cache
            context_str = json.dumps(context, sort_keys=True)
            cache_key = self._generate_cache_key(user_input, context_str)
            cached_result = self.cache.get(cache_key)
            
            if cached_result:
                self.logger.info("cache_hit", user_input=user_input)
                latency = (time.time() - start_time) * 1000
                self.metrics.observe("translation_latency_ms", latency)
                return cached_result
            
            # Check circuit breaker
            if not self.circuit_breaker.should_allow_request():
                self.logger.warning("circuit_breaker_open", user_input=user_input)
                # Try fallback
                return await self._fallback_translation(user_input)
            
            # Call LLM with retry
            result = await self._call_llm_with_retry_wrapper(user_input, context)
            
            if result:
                # Cache the result
                self.cache.set(cache_key, result)
                self.circuit_breaker.record_success()
            else:
                self.circuit_breaker.record_failure()
            
            latency = (time.time() - start_time) * 1000
            self.metrics.observe("translation_latency_ms", latency)
            self.metrics.increment("translations_total")
            
            return result
            
        except Exception as e:
            self.logger.error("translation_error", 
                            user_input=user_input,
                            error=str(e))
            self.circuit_breaker.record_failure()
            self.metrics.increment("translation_errors")
            
            # Try fallback
            return await self._fallback_translation(user_input)
    
    async def _call_llm_with_retry_wrapper(self, user_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call LLM with retry logic wrapper"""
        last_exception = None
        
        for attempt in range(self.config.retry_max_attempts):
            try:
                result = await self._call_llm(user_input, context)
                if attempt > 0:
                    self.logger.info("retry_succeeded", attempt=attempt)
                    self.metrics.increment("retry_success")
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.config.retry_max_attempts - 1:
                    delay = min(
                        self.config.retry_max_delay,
                        self.config.retry_base_delay * (self.config.retry_exponential_base ** attempt)
                    )
                    
                    if self.config.retry_jitter:
                        delay += random.uniform(0, delay * 0.1)
                    
                    self.logger.warning("retry_attempt", 
                                     attempt=attempt + 1,
                                     delay=delay,
                                     error=str(e))
                    self.metrics.increment("retry_attempt")
                    
                    await asyncio.sleep(delay)
                else:
                    self.logger.error("retry_exhausted", 
                                   attempts=self.config.retry_max_attempts,
                                   error=str(e))
                    self.metrics.increment("retry_exhausted")
        
        raise last_exception
    
    async def _call_llm(self, user_input: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Call LLM without retry logic"""
        context_str = f"Current directory: {context.get('cwd', '/')}\n"
        context_str += f"Operating System: {context.get('os', 'Linux')}\n"
        
        response = await asyncio.wait_for(
            self.client.chat.completions.create(
                model=self.config.llm_model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context_str + user_input}
                ],
                temperature=self.config.llm_temperature,
                max_tokens=self.config.llm_max_tokens
            ),
            timeout=self.config.llm_timeout
        )
        
        llm_output = response.choices[0].message.content
        return self._parse_llm_response(llm_output)
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM JSON response"""
        try:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return None
        except json.JSONDecodeError:
            return None
    
    async def _fallback_translation(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Fallback translation using alternative models or rules"""
        self.logger.info("using_fallback", user_input=user_input)
        self.metrics.increment("fallback_used")
        
        # Try fallback models
        for fallback_model in self.config.fallback_models:
            try:
                self.logger.info("trying_fallback_model", model=fallback_model)
                
                # Temporarily switch model
                original_model = self.config.llm_model
                self.config.llm_model = fallback_model
                
                result = await self._call_llm(user_input, {"cwd": os.getcwd(), "os": "Linux"})
                
                # Restore original model
                self.config.llm_model = original_model
                
                if result:
                    return result
                    
            except Exception as e:
                self.logger.warning("fallback_model_failed", 
                                  model=fallback_model,
                                  error=str(e))
                continue
        
        # Ultimate fallback: return error message
        return {
            "command": "",
            "explanation": "Service temporarily unavailable. Please try again.",
            "warning": "All LLM services are currently unavailable.",
            "safe": False
        }


# ============================================================================
# BACKGROUND TASK QUEUE
# ============================================================================

@dataclass
class Task:
    """Background task"""
    id: str
    func: Any
    args: tuple
    kwargs: dict
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def __lt__(self, other):
        return self.priority < other.priority


class TaskQueue:
    """Background task queue with worker pool"""
    
    def __init__(self, config: Config, logger: StructuredLogger, metrics: Metrics):
        self.config = config
        self.logger = logger
        self.metrics = metrics
        self.queue: asyncio.PriorityQueue = asyncio.PriorityQueue(maxsize=config.task_queue_max_size)
        self.workers: List[asyncio.Task] = []
        self.running = False
    
    async def start(self):
        """Start worker pool"""
        self.running = True
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.config.task_queue_workers)
        ]
        self.logger.info("task_queue_started", workers=len(self.workers))
    
    async def stop(self):
        """Stop worker pool"""
        self.running = False
        for worker in self.workers:
            worker.cancel()
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.logger.info("task_queue_stopped")
    
    async def enqueue(self, func, *args, priority: int = 0, **kwargs) -> str:
        """Enqueue a task"""
        task_id = hashlib.md5(f"{time.time()}{random.random()}".encode()).hexdigest()[:8]
        task = Task(task_id, func, args, kwargs, priority)
        
        try:
            await asyncio.wait_for(
                self.queue.put((priority, task)),
                timeout=1.0
            )
            self.metrics.increment("tasks_enqueued")
            self.metrics.set_gauge("queue_size", self.queue.qsize())
            return task_id
        except asyncio.TimeoutError:
            self.logger.error("queue_full")
            self.metrics.increment("tasks_rejected")
            raise
    
    async def _worker(self, worker_id: int):
        """Worker coroutine"""
        self.logger.info("worker_started", worker_id=worker_id)
        
        while self.running:
            try:
                # Get task from queue
                priority, task = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )
                
                self.metrics.set_gauge("queue_size", self.queue.qsize())
                
                # Execute task
                start_time = time.time()
                try:
                    await task.func(*task.args, **task.kwargs)
                    latency = (time.time() - start_time) * 1000
                    self.metrics.observe("task_duration_ms", latency)
                    self.metrics.increment("tasks_completed")
                    
                except Exception as e:
                    self.logger.error("task_failed", 
                                    task_id=task.id,
                                    error=str(e))
                    self.metrics.increment("tasks_failed")
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error("worker_error", 
                                worker_id=worker_id,
                                error=str(e))


# ============================================================================
# ENTERPRISE GPT SHELL
# ============================================================================

class EnterpriseGPTShell:
    """Enterprise-grade GPT-OS shell"""
    
    def __init__(self):
        # Configuration
        self.config = Config.from_env()
        
        # Observability
        self.logger = StructuredLogger("gpt-os", self.config.log_level)
        self.metrics = Metrics()
        
        # Resilience components
        self.circuit_breaker = CircuitBreaker(self.config, self.logger, self.metrics)
        self.cache = LRUCache(self.config, self.logger, self.metrics)
        self.rate_limiter = TokenBucket(self.config, self.logger)
        self.memory_manager = MemoryManager(self.config, self.logger, self.metrics)
        
        # Services
        self.llm_service = LLMService(
            self.config, self.logger, self.metrics,
            self.circuit_breaker, self.cache, self.rate_limiter
        )
        self.task_queue = TaskQueue(self.config, self.logger, self.metrics)
        
        # State
        self.username = os.getenv('USER', 'user')
        self.hostname = os.uname().nodename
        self.dangerous_commands = [
            'rm -rf', 'mkfs', 'dd', 'format', 'fdisk',
            'shutdown', 'reboot', 'init 0', 'init 6',
            'kill -9', 'killall', ':(){:|:&};:',
        ]
        
        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
    
    async def initialize(self):
        """Initialize async components"""
        self.logger.info("initializing_gpt_os", version="2.0")
        
        # Start task queue
        await self.task_queue.start()
        
        # Start background tasks
        self.background_tasks.append(
            asyncio.create_task(self.memory_manager.periodic_gc())
        )
        self.background_tasks.append(
            asyncio.create_task(self._periodic_cache_cleanup())
        )
        self.background_tasks.append(
            asyncio.create_task(self._health_check())
        )
        
        self.logger.info("gpt_os_initialized")
    
    async def shutdown(self):
        """Graceful shutdown"""
        self.logger.info("shutting_down_gpt_os")
        
        # Stop task queue
        await self.task_queue.stop()
        
        # Cancel background tasks
        for task in self.background_tasks:
            task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        
        self.logger.info("gpt_os_shutdown_complete")
    
    async def _periodic_cache_cleanup(self):
        """Periodic cache cleanup"""
        while True:
            await asyncio.sleep(300)  # 5 minutes
            self.cache.cleanup_expired()
    
    async def _health_check(self):
        """Periodic health check"""
        while True:
            await asyncio.sleep(self.config.health_check_interval)
            
            health = {
                "status": "healthy",
                "circuit_breaker": self.circuit_breaker.state.value,
                "cache_size": len(self.cache.cache),
                "queue_size": self.task_queue.queue.qsize(),
                "history_size": len(self.memory_manager.history)
            }
            
            self.logger.debug("health_check", **health)
    
    def print_banner(self):
        """Display banner"""
        banner = """
╔═══════════════════════════════════════════════════════════════╗
║                      GPT-OS Enterprise v2.0                   ║
║          Production-Grade AI-Powered Linux Shell              ║
║                                                               ║
║  ✨ Async Operations  🔄 Circuit Breaker  💾 Smart Cache    ║
║  🔁 Auto-Retry  📊 Observability  🛡️  Enterprise Security   ║
╚═══════════════════════════════════════════════════════════════╝
"""
        print(banner)
    
    def get_prompt(self) -> str:
        """Generate prompt"""
        cwd = os.getcwd()
        home = os.path.expanduser('~')
        if cwd.startswith(home):
            cwd = '~' + cwd[len(home):]
        return f"\n🚀 {self.username}@{self.hostname}:{cwd}$ "
    
    async def translate_and_execute(self, user_input: str):
        """Translate and execute command"""
        start_time = time.time()
        
        try:
            # Translate
            print("\n🤔 Thinking...")
            context = {
                "cwd": os.getcwd(),
                "os": os.uname().sysname
            }
            
            result = await self.llm_service.translate_command(user_input, context)
            
            if not result:
                print("❌ Sorry, I couldn't process that request. Please try again.")
                return
            
            command = result.get('command', '')
            explanation = result.get('explanation', '')
            warning = result.get('warning')
            safe = result.get('safe', True)
            
            # Display
            print("\n💡 I understand! Here's what I'll do:")
            print("─" * 70)
            print(f"Command: {command}")
            print(f"Explanation: {explanation}")
            
            if warning:
                print(f"\n{warning}")
            
            # Confirm
            if not safe or self._is_dangerous(command):
                confirm = input("\n⚠️  This command may be dangerous. Execute? (yes/no): ").strip().lower()
            else:
                confirm = input("\n▶️  Execute this command? (yes/no): ").strip().lower()
            
            if confirm not in ['yes', 'y']:
                print("❌ Command cancelled.")
                return
            
            # Execute
            print(f"\n⚙️  Executing...")
            exit_code, stdout, stderr = await self._execute_command(command)
            
            # Store in history
            self.memory_manager.add_to_history({
                'input': user_input,
                'command': command,
                'exit_code': exit_code,
                'timestamp': datetime.now().isoformat()
            })
            
            # Display output
            self._format_output(stdout, stderr, exit_code)
            
            # Metrics
            latency = (time.time() - start_time) * 1000
            self.metrics.observe("command_total_latency_ms", latency)
            self.metrics.increment("commands_executed")
            
        except Exception as e:
            self.logger.error("command_execution_error", error=str(e))
            print(f"\n❌ Error: {str(e)}")
    
    def _is_dangerous(self, command: str) -> bool:
        """Check if command is dangerous"""
        return any(dangerous in command.lower() for dangerous in self.dangerous_commands)
    
    async def _execute_command(self, command: str) -> Tuple[int, str, str]:
        """Execute command asynchronously"""
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.config.command_timeout
            )
            
            return process.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            return -1, "", "Command timed out"
        except Exception as e:
            return -1, "", str(e)
    
    def _format_output(self, stdout: str, stderr: str, exit_code: int):
        """Format command output"""
        if exit_code == 0:
            if stdout.strip():
                print("\n✅ Output:")
                print("─" * 70)
                lines = stdout.split('\n')
                if len(lines) > self.config.command_max_output_lines:
                    print('\n'.join(lines[:self.config.command_max_output_lines]))
                    print(f"\n... ({len(lines) - self.config.command_max_output_lines} more lines)")
                else:
                    print(stdout)
        else:
            print(f"\n❌ Command failed with exit code {exit_code}")
            if stderr.strip():
                print("Error details:")
                print("─" * 70)
                print(stderr)
    
    def show_help(self):
        """Show help"""
        help_text = """
╔═══════════════════════════════════════════════════════════════╗
║                   GPT-OS ENTERPRISE HELP                      ║
╚═══════════════════════════════════════════════════════════════╝

🗣️  Natural Language Commands:
   Just type what you want in plain English!

🔧 Built-in Commands:
   • help     - Show this help
   • history  - Show command history
   • stats    - Show system statistics
   • health   - Show health status
   • clear    - Clear screen
   • exit     - Exit GPT-OS

💡 Enterprise Features:
   • Async operations for better performance
   • Circuit breaker prevents cascading failures
   • Smart caching reduces latency
   • Auto-retry with exponential backoff
   • Rate limiting prevents abuse
   • Memory management with auto-GC
"""
        print(help_text)
    
    def show_stats(self):
        """Show statistics"""
        stats = self.metrics.get_stats()
        print("\n📊 System Statistics:")
        print("─" * 70)
        print(json.dumps(stats, indent=2))
    
    def show_health(self):
        """Show health status"""
        health = {
            "circuit_breaker": self.circuit_breaker.state.value,
            "cache_size": len(self.cache.cache),
            "queue_size": self.task_queue.queue.qsize(),
            "history_size": len(self.memory_manager.history)
        }
        print("\n🏥 Health Status:")
        print("─" * 70)
        print(json.dumps(health, indent=2))
    
    def show_history(self):
        """Show history"""
        history = self.memory_manager.get_history(limit=20)
        if not history:
            print("📜 No command history yet.")
            return
        
        print("\n📜 Command History (last 20):")
        print("─" * 70)
        for i, entry in enumerate(history, 1):
            print(f"{i}. {entry['input']}")
            print(f"   → {entry['command']}")
            print()
    
    async def run(self):
        """Main shell loop"""
        await self.initialize()
        self.print_banner()
        
        try:
            while True:
                try:
                    user_input = await asyncio.get_event_loop().run_in_executor(
                        None, input, self.get_prompt()
                    )
                    user_input = user_input.strip()
                    
                    if not user_input:
                        continue
                    
                    # Built-in commands
                    if user_input.lower() in ['exit', 'quit', 'q']:
                        print("\n👋 Goodbye!")
                        break
                    elif user_input.lower() in ['help', '?']:
                        self.show_help()
                        continue
                    elif user_input.lower() == 'stats':
                        self.show_stats()
                        continue
                    elif user_input.lower() == 'health':
                        self.show_health()
                        continue
                    elif user_input.lower() == 'history':
                        self.show_history()
                        continue
                    elif user_input.lower() == 'clear':
                        os.system('clear')
                        continue
                    
                    # Direct command
                    if user_input.startswith('!'):
                        command = user_input[1:].strip()
                        print(f"\n🔧 Executing: {command}")
                        exit_code, stdout, stderr = await self._execute_command(command)
                        self._format_output(stdout, stderr, exit_code)
                        continue
                    
                    # Translate and execute
                    await self.translate_and_execute(user_input)
                    
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted. Type 'exit' to quit.")
                    continue
                except Exception as e:
                    self.logger.error("shell_error", error=str(e))
                    print(f"\n❌ Error: {str(e)}")
                    continue
        
        finally:
            await self.shutdown()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""
    shell = EnterpriseGPTShell()
    await shell.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
