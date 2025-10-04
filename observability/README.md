# 🔍 Observability Framework

Production-grade observability scaffold for MAGSASA-CARD-ERP with **metrics**, **tracing**, and **structured logging**.

## 📁 Structure

```
observability/
├── metrics/              # Prometheus metrics instrumentation
│   └── metrics_middleware.py
├── tracing/              # OpenTelemetry distributed tracing
│   └── otel_tracer.py
├── logging/              # Structured JSON logging
│   └── structured_logger.py
└── dashboards/           # Grafana dashboards & alert rules
    ├── service_dashboard.json
    └── alert_rules.yml
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install prometheus-client opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-flask opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-sqlalchemy opentelemetry-exporter-otlp-proto-grpc
```

Or add to `requirements.txt`:

```txt
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-flask>=0.42b0
opentelemetry-instrumentation-requests>=0.42b0
opentelemetry-instrumentation-sqlalchemy>=0.42b0
opentelemetry-exporter-otlp-proto-grpc>=1.21.0
```

### 2. Integrate into Your Flask App

```python
from flask import Flask
from observability.metrics.metrics_middleware import MetricsMiddleware
from observability.tracing.otel_tracer import init_tracing, get_tracer
from observability.logging.structured_logger import get_logger

app = Flask(__name__)

# ✅ Enable metrics collection
MetricsMiddleware(app)

# ✅ Enable distributed tracing
init_tracing(app, service_name="magsasa-card-erp")

# ✅ Get structured logger
logger = get_logger(__name__)
tracer = get_tracer(__name__)

@app.route('/api/process')
def process_data():
    with tracer.start_as_current_span("process_data"):
        logger.info("Processing started", user_id="123")
        
        # Your business logic here
        result = {"status": "success"}
        
        logger.info("Processing completed", result=result)
        return result

if __name__ == '__main__':
    app.run()
```

### 3. Access Metrics

Metrics are automatically exposed at:

```
http://localhost:8000/metrics
```

## 📊 Metrics

The middleware automatically tracks:

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | method, endpoint, status_code | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request latency distribution |
| `http_requests_exceptions_total` | Counter | method, endpoint, exception_type | Exceptions raised |

### Custom Metrics

Track custom function metrics:

```python
from observability.metrics.metrics_middleware import track_function_metrics

@track_function_metrics("payment_processing")
def process_payment(order_id):
    # Business logic
    pass
```

This creates:
- `payment_processing_calls_total{status="success|error"}`
- `payment_processing_duration_seconds`

## 🧭 Distributed Tracing

### Auto-Instrumentation

Flask, SQLAlchemy, and HTTP requests are automatically instrumented.

### Manual Spans

```python
from observability.tracing.otel_tracer import get_tracer, add_span_attributes, add_span_event

tracer = get_tracer(__name__)

with tracer.start_as_current_span("complex_operation"):
    add_span_attributes(user_id="123", order_id="456")
    
    # Business logic
    add_span_event("validation_completed", {"items": 5})
    
    # More logic
    add_span_event("payment_processed", {"amount": 1000})
```

### Trace Context in Logs

Logs automatically include `trace_id` and `span_id` for correlation.

## 🪵 Structured Logging

All logs are JSON-formatted with trace context:

```python
from observability.logging.structured_logger import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Order created")

# With structured fields
logger.info("Payment processed", 
    order_id="12345", 
    amount=1000, 
    currency="PHP"
)

# Error logging
logger.error("Payment failed", 
    error="Insufficient funds", 
    user_id="123"
)
```

### Log Format

```json
{
  "timestamp": "2025-10-03T10:15:30.123456Z",
  "level": "INFO",
  "logger": "src.routes.order",
  "message": "Payment processed",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "order_id": "12345",
  "amount": 1000,
  "currency": "PHP",
  "module": "order",
  "function": "process_payment",
  "line": 42
}
```

## 🐳 Local Development with Docker

Use the provided `docker-compose.yml` to run Prometheus + Grafana locally:

```bash
docker-compose -f observability/docker-compose.yml up -d
```

Access:
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

The service dashboard will be automatically provisioned in Grafana.

## 📈 Dashboards & Alerts

### Import Dashboard

1. Go to Grafana → Dashboards → Import
2. Upload `dashboards/service_dashboard.json`
3. Select Prometheus as the data source

### Dashboard Panels

- **Request Rate (QPS)**: Total and per-endpoint request rates
- **Request Latency**: p50, p95, p99 percentiles
- **Error Rate**: 4xx and 5xx error percentages
- **Top Endpoints**: Most trafficked endpoints
- **Exception Rate**: Exceptions by type
- **Status Code Distribution**: HTTP status code breakdown
- **Request Duration Heatmap**: Latency distribution over time

### Alert Rules

Load alert rules into Prometheus:

```yaml
# prometheus.yml
rule_files:
  - /path/to/observability/dashboards/alert_rules.yml
```

Alert conditions:
- 🔴 **High 5xx Error Rate**: > 5% for 2 minutes
- 🟡 **High Request Latency**: p95 > 2s for 5 minutes
- 🟡 **Exception Spike**: > 1/sec for 2 minutes
- 🔴 **Service Down**: Service unreachable for 1 minute
- 🟡 **Abnormal Request Rate**: > 1000 req/sec or < 0.1 req/sec

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTEL_SERVICE_NAME` | Service name for tracing | `magsasa-card-erp` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | None (console only) |
| `ENVIRONMENT` | Deployment environment | `development` |

### Example with Jaeger

```bash
# Start Jaeger
docker run -d --name jaeger \
  -p 4317:4317 \
  -p 16686:16686 \
  jaegertracing/all-in-one:latest

# Configure your app
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317

# Access Jaeger UI
open http://localhost:16686
```

## 🧪 CI/CD Integration

See `.github/workflows/observability.yml` for the CI gate that enforces observability hooks in every PR.

The gate ensures that code changes include:
- Metrics tracking (`metrics_client`)
- Distributed tracing (`start_as_current_span`)
- Structured logging (`logger.info`)

## 📚 Best Practices

### 1. Log Strategically

✅ **DO:**
```python
logger.info("Order created", order_id=order.id, user_id=user.id)
logger.error("Payment failed", error=str(e), order_id=order.id)
```

❌ **DON'T:**
```python
logger.info(f"Order {order.id} created by {user.id}")  # Not structured
print("Payment failed")  # Not logged
```

### 2. Trace Business Operations

✅ **DO:**
```python
with tracer.start_as_current_span("process_order"):
    add_span_attributes(order_id=order.id, items=len(order.items))
    validate_order(order)
    add_span_event("order_validated")
    process_payment(order)
```

❌ **DON'T:**
```python
# No tracing context
validate_order(order)
process_payment(order)
```

### 3. Use Custom Metrics for Business KPIs

```python
from prometheus_client import Counter, Gauge

orders_created = Counter('orders_created_total', 'Total orders created')
active_users = Gauge('active_users', 'Number of active users')

@app.route('/api/orders', methods=['POST'])
def create_order():
    order = create_new_order()
    orders_created.inc()  # Track business metric
    return {"order_id": order.id}
```

## 🎯 Next Steps

1. **Set up alerting**: Configure Prometheus Alertmanager with Slack/PagerDuty
2. **Create SLOs**: Define Service Level Objectives (99.9% uptime, p95 < 200ms)
3. **Log aggregation**: Send logs to ELK/Loki for centralized analysis
4. **APM integration**: Connect to Datadog/New Relic for advanced APM

## 🤝 Contributing

When adding new features:

1. Add appropriate metrics for the feature
2. Wrap critical operations in trace spans
3. Use structured logging with business context
4. Update dashboards if new metrics are added

## 📖 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)
- [Three Pillars of Observability](https://www.oreilly.com/library/view/distributed-systems-observability/9781492033431/)

