# GPT-OS Monitoring & Observability Guide

## Overview

GPT-OS Enterprise v2.0 includes comprehensive monitoring, logging, and health check systems for production deployment.

## Structured Logging

### Log Format

All logs are output in JSON format for easy parsing and analysis:

```json
{
  "timestamp": "2026-02-08T12:00:00Z",
  "level": "INFO",
  "event": "command_translated",
  "user_input": "update my software",
  "command": "sudo apt update",
  "latency_ms": 234,
  "cache_hit": false
}
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages for potential issues
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

### Key Events Logged

| Event | Level | Description |
|-------|-------|-------------|
| `gpt_os_initialized` | INFO | System startup complete |
| `command_translated` | INFO | Command successfully translated |
| `cache_hit` | INFO | Cache hit for translation |
| `cache_miss` | INFO | Cache miss for translation |
| `circuit_breaker_opened` | WARNING | Circuit breaker opened due to failures |
| `circuit_breaker_closed` | INFO | Circuit breaker closed after recovery |
| `rate_limited` | WARNING | Request rate limited |
| `retry_attempt` | WARNING | Retrying failed request |
| `fallback_used` | INFO | Using fallback LLM model |
| `translation_error` | ERROR | Error during translation |
| `task_failed` | ERROR | Background task failed |

## Metrics Collection

### Available Metrics

#### Counters
- `translations_total` - Total number of translations
- `commands_executed` - Total commands executed
- `cache_hit` - Cache hits
- `cache_miss` - Cache misses
- `cache_eviction` - Cache evictions
- `retry_attempt` - Retry attempts
- `retry_success` - Successful retries
- `retry_exhausted` - Exhausted retries
- `fallback_used` - Fallback model usage
- `translation_errors` - Translation errors
- `tasks_enqueued` - Tasks enqueued
- `tasks_completed` - Tasks completed
- `tasks_failed` - Failed tasks
- `tasks_rejected` - Rejected tasks (queue full)
- `gc_runs` - Garbage collection runs

#### Gauges
- `circuit_breaker_state` - Circuit breaker state (0=CLOSED, 0.5=HALF_OPEN, 1=OPEN)
- `cache_size` - Current cache size
- `queue_size` - Current task queue size
- `history_size` - Current history size

#### Histograms
- `translation_latency_ms` - Translation latency in milliseconds
- `command_total_latency_ms` - Total command latency
- `task_duration_ms` - Task duration

### Viewing Metrics

Use the `stats` command in the shell:

```bash
🚀 user@host:~$ stats

📊 System Statistics:
──────────────────────────────────────────────────────────────────
{
  "counters": {
    "translations_total": 42,
    "commands_executed": 38,
    "cache_hit": 15,
    "cache_miss": 27
  },
  "gauges": {
    "circuit_breaker_state": 0,
    "cache_size": 27,
    "queue_size": 0,
    "history_size": 38
  },
  "histograms": {
    "translation_latency_ms": {
      "count": 42,
      "min": 123,
      "max": 2456,
      "avg": 456.7
    }
  }
}
```

## Health Checks

### Health Check Types

#### 1. Liveness Probe
**Purpose**: Is the service running?

**Check**: Basic service availability

**Command**:
```bash
🚀 user@host:~$ health
```

**Response**:
```json
{
  "status": "healthy",
  "circuit_breaker": "closed",
  "cache_size": 27,
  "queue_size": 0,
  "history_size": 38
}
```

#### 2. Readiness Probe
**Purpose**: Can the service handle requests?

**Checks**:
- Circuit breaker not OPEN
- Queue not full
- Memory within limits

#### 3. Startup Probe
**Purpose**: Has initialization completed?

**Checks**:
- LLM client initialized
- Task queue started
- Background tasks running

### Health Check Intervals

- **Liveness**: Every 30 seconds
- **Readiness**: Every 10 seconds
- **Startup**: Every 5 seconds (during startup only)

### Health Status Codes

| Status | Code | Description |
|--------|------|-------------|
| Healthy | 200 | All checks passed |
| Degraded | 200 | Some non-critical issues |
| Unhealthy | 503 | Critical issues present |

## Circuit Breaker Monitoring

### States

1. **CLOSED** (Normal)
   - All requests pass through
   - Failures are counted
   - Metric value: 0

2. **OPEN** (Failing)
   - Requests fail fast
   - No calls to LLM
   - Metric value: 1

3. **HALF_OPEN** (Testing)
   - Limited requests allowed
   - Testing recovery
   - Metric value: 0.5

### State Transitions

```
CLOSED → OPEN: After 5 consecutive failures
OPEN → HALF_OPEN: After 60 seconds recovery timeout
HALF_OPEN → CLOSED: After 2 consecutive successes
HALF_OPEN → OPEN: On any failure
```

### Monitoring Circuit Breaker

Check current state:
```bash
🚀 user@host:~$ health
```

Look for `circuit_breaker` field in response.

## Cache Performance

### Cache Metrics

- **Hit Ratio**: `cache_hit / (cache_hit + cache_miss)`
- **Size**: Current number of entries
- **Evictions**: Number of entries evicted

### Optimal Performance

- **Hit Ratio**: > 70%
- **Size**: < 80% of max_size
- **Evictions**: < 10% of total requests

### Cache Tuning

Adjust in environment variables:

```bash
export GPTOS_CACHE_MAX_SIZE=2000  # Increase cache size
export GPTOS_CACHE_TTL=7200       # Increase TTL to 2 hours
```

## Performance Monitoring

### Key Performance Indicators (KPIs)

| KPI | Target | Alert Threshold |
|-----|--------|-----------------|
| P50 Latency | < 500ms | > 1000ms |
| P95 Latency | < 2s | > 5s |
| P99 Latency | < 5s | > 10s |
| Error Rate | < 0.1% | > 1% |
| Cache Hit Ratio | > 70% | < 50% |
| Circuit Breaker Opens | 0/hour | > 5/hour |

### Latency Breakdown

```
Total Latency = Cache Lookup + LLM Call + Parsing + Execution
                (< 1ms)      (200-2000ms)  (< 10ms)  (100-5000ms)
```

### Bottleneck Identification

1. **High latency with low cache hit ratio**
   - Solution: Increase cache size or TTL

2. **High latency with high cache hit ratio**
   - Solution: Check LLM service performance

3. **Frequent circuit breaker opens**
   - Solution: Check LLM service availability, adjust thresholds

4. **High memory usage**
   - Solution: Reduce history size, cache size, or queue size

## Memory Management

### Memory Metrics

- **History Size**: Current number of history entries
- **Cache Size**: Current number of cache entries
- **Queue Size**: Current number of queued tasks

### Memory Limits

```python
# Default configuration
max_history: 1000 entries
cache_max_size: 1000 entries
task_queue_max_size: 100 tasks
```

### Garbage Collection

Automatic garbage collection runs every 5 minutes:
- Removes expired cache entries
- Triggers Python GC
- Logs collected objects

Monitor GC runs:
```bash
🚀 user@host:~$ stats
# Look for "gc_runs" counter
```

## Rate Limiting

### Configuration

- **Requests per minute**: 60
- **Burst size**: 10

### Monitoring Rate Limits

Watch for `rate_limited` events in logs:

```json
{
  "timestamp": "2026-02-08T12:00:00Z",
  "level": "WARNING",
  "event": "rate_limited",
  "user_input": "..."
}
```

### Adjusting Rate Limits

```bash
export GPTOS_RATE_LIMIT_RPM=120    # Increase to 120 requests/min
export GPTOS_RATE_LIMIT_BURST=20   # Increase burst to 20
```

## Alerting Recommendations

### Critical Alerts

1. **Circuit Breaker Open**
   - Condition: `circuit_breaker_state == 1`
   - Action: Check LLM service availability

2. **High Error Rate**
   - Condition: `translation_errors / translations_total > 0.05`
   - Action: Investigate error logs

3. **Memory Exhaustion**
   - Condition: `queue_size >= task_queue_max_size`
   - Action: Increase queue size or add workers

### Warning Alerts

1. **Low Cache Hit Ratio**
   - Condition: `cache_hit / (cache_hit + cache_miss) < 0.5`
   - Action: Increase cache size or TTL

2. **High Latency**
   - Condition: `P95(translation_latency_ms) > 5000`
   - Action: Check LLM service performance

3. **Frequent Retries**
   - Condition: `retry_attempt / translations_total > 0.2`
   - Action: Investigate LLM service stability

## Log Aggregation

### Recommended Setup

1. **Fluentd/Fluent Bit**
   - Collect JSON logs
   - Forward to Elasticsearch

2. **Elasticsearch**
   - Store and index logs
   - Enable full-text search

3. **Kibana**
   - Visualize logs
   - Create dashboards

### Sample Fluentd Config

```xml
<source>
  @type tail
  path /var/log/gpt-os/*.log
  pos_file /var/log/gpt-os/gpt-os.pos
  tag gpt-os
  format json
</source>

<match gpt-os>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name gpt-os
  type_name _doc
</match>
```

## Metrics Exporter (Future)

### Prometheus Integration

Future versions will include Prometheus metrics exporter:

```python
# Expose metrics endpoint
from prometheus_client import start_http_server, Counter, Histogram, Gauge

translations_counter = Counter('gptos_translations_total', 'Total translations')
latency_histogram = Histogram('gptos_translation_latency_seconds', 'Translation latency')
circuit_breaker_gauge = Gauge('gptos_circuit_breaker_state', 'Circuit breaker state')

# Start metrics server
start_http_server(9090)
```

Access metrics at: `http://localhost:9090/metrics`

## Distributed Tracing (Future)

### OpenTelemetry Integration

Future versions will include distributed tracing:

```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Instrument code
with tracer.start_as_current_span("translate_command"):
    result = await llm_service.translate_command(user_input, context)
```

## Troubleshooting

### Common Issues

#### 1. High Latency

**Symptoms**: Slow command translation

**Diagnosis**:
```bash
🚀 user@host:~$ stats
# Check translation_latency_ms histogram
```

**Solutions**:
- Check cache hit ratio
- Verify LLM service performance
- Increase cache TTL

#### 2. Circuit Breaker Open

**Symptoms**: "Circuit breaker open" messages

**Diagnosis**:
```bash
🚀 user@host:~$ health
# Check circuit_breaker state
```

**Solutions**:
- Verify LLM API key
- Check network connectivity
- Wait for recovery timeout (60s)

#### 3. Memory Growth

**Symptoms**: Increasing memory usage

**Diagnosis**:
```bash
🚀 user@host:~$ stats
# Check history_size, cache_size, queue_size
```

**Solutions**:
- Reduce max_history
- Reduce cache_max_size
- Increase GC interval

#### 4. Rate Limiting

**Symptoms**: "Rate limited" messages

**Diagnosis**: Check logs for `rate_limited` events

**Solutions**:
- Increase rate limit
- Implement request queuing
- Add caching

## Best Practices

1. **Monitor continuously**: Set up automated monitoring
2. **Alert proactively**: Configure alerts before issues occur
3. **Log everything**: Comprehensive logging aids debugging
4. **Analyze trends**: Look for patterns in metrics
5. **Tune configuration**: Adjust based on observed behavior
6. **Test resilience**: Regularly test failure scenarios
7. **Document incidents**: Keep runbooks for common issues

## Conclusion

GPT-OS Enterprise v2.0 provides comprehensive observability through structured logging, metrics collection, and health checks. Use these tools to monitor, troubleshoot, and optimize your deployment.

---

**Version**: 2.0
**Last Updated**: February 8, 2026
