# 🧩 STAGE 6.7 — OBSERVABILITY & CI ENFORCEMENT

**Status:** ✅ **COMPLETED**

Production-grade observability scaffold with **metrics**, **tracing**, **structured logging**, and **CI enforcement** for MAGSASA-CARD-ERP.

---

## 📋 Overview

This stage implements a comprehensive observability framework that ensures:

1. **📊 Metrics** - Prometheus-based metrics for request rates, latency, and errors
2. **🧭 Distributed Tracing** - OpenTelemetry tracing for request flow visualization
3. **🪵 Structured Logging** - JSON logs with automatic trace context injection
4. **🚨 Alerting** - Prometheus alerting rules for anomaly detection
5. **📈 Dashboards** - Grafana dashboards for service health monitoring
6. **🔒 CI Enforcement** - GitHub Actions gate that blocks PRs without observability hooks

---

## 📁 Directory Structure

```
observability/
├── metrics/
│   ├── __init__.py
│   └── metrics_middleware.py          # Prometheus metrics instrumentation
├── tracing/
│   ├── __init__.py
│   └── otel_tracer.py                 # OpenTelemetry tracing setup
├── logging/
│   ├── __init__.py
│   └── structured_logger.py           # JSON logging with trace context
├── dashboards/
│   ├── __init__.py
│   ├── service_dashboard.json         # Grafana dashboard config
│   └── alert_rules.yml                # Prometheus alert rules
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yml        # Auto-provision Prometheus & Jaeger
│       └── dashboards/
│           └── dashboards.yml         # Auto-provision dashboards
├── docker-compose.yml                 # Complete observability stack
├── prometheus.yml                     # Prometheus configuration
├── alertmanager.yml                   # Alertmanager configuration
├── observability_requirements.txt     # Python dependencies
├── README.md                          # Full documentation
└── QUICKSTART.md                      # 5-minute setup guide

scripts/
└── check_observability_hooks.py       # CI gate script

.github/
└── workflows/
    └── observability.yml               # GitHub Actions CI workflow
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r observability/observability_requirements.txt
```

### 2. Start Observability Stack

```bash
cd observability/
docker-compose up -d
```

### 3. Run Your Application

The application is already instrumented! Just run:

```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8000
python src/main.py
```

### 4. Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Jaeger (Tracing)**: http://localhost:16686
- **Metrics Endpoint**: http://localhost:8000/metrics

See [`observability/QUICKSTART.md`](observability/QUICKSTART.md) for detailed instructions.

---

## 🎯 What's Included

### 📊 Metrics (`observability/metrics/`)

Automatic instrumentation of:
- ✅ HTTP request counts (`http_requests_total`)
- ✅ Request latency histograms (`http_request_duration_seconds`)
- ✅ Exception counters (`http_requests_exceptions_total`)

**Usage:**
```python
from observability.metrics.metrics_middleware import MetricsMiddleware

app = Flask(__name__)
MetricsMiddleware(app)  # Automatically instruments all routes
```

**Custom Metrics:**
```python
from observability.metrics.metrics_middleware import track_function_metrics

@track_function_metrics("payment_processing")
def process_payment(order_id):
    # Business logic
    pass
```

---

### 🧭 Distributed Tracing (`observability/tracing/`)

Auto-instruments Flask, SQLAlchemy, and HTTP requests with OpenTelemetry.

**Usage:**
```python
from observability.tracing.otel_tracer import init_tracing, get_tracer

app = Flask(__name__)
init_tracing(app, otlp_endpoint="http://localhost:4317")

tracer = get_tracer(__name__)

@app.route('/api/process')
def process_data():
    with tracer.start_as_current_span("process_data"):
        # Business logic
        return {"status": "ok"}
```

**Features:**
- ✅ Automatic trace propagation
- ✅ Trace context in logs (trace_id, span_id)
- ✅ Custom spans and events
- ✅ Jaeger/Tempo/Datadog export support

---

### 🪵 Structured Logging (`observability/logging/`)

JSON-formatted logs with automatic trace context injection.

**Usage:**
```python
from observability.logging.structured_logger import get_logger

logger = get_logger(__name__)

logger.info("Order created", order_id="12345", user_id="123", amount=1000)
logger.error("Payment failed", error="Insufficient funds", order_id="12345")
```

**Output:**
```json
{
  "timestamp": "2025-10-03T10:15:30.123456Z",
  "level": "INFO",
  "logger": "src.routes.order",
  "message": "Order created",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "order_id": "12345",
  "user_id": "123",
  "amount": 1000
}
```

---

### 📈 Dashboards (`observability/dashboards/`)

Pre-built Grafana dashboard with panels for:

- **Request Rate (QPS)**: Total and per-endpoint traffic
- **Request Latency**: p50, p95, p99 percentiles
- **Error Rate**: 4xx and 5xx error percentages
- **Top Endpoints**: Most trafficked routes
- **Exception Rate**: Exception tracking by type
- **Status Code Distribution**: HTTP status breakdown
- **Request Duration Heatmap**: Latency over time

Dashboard automatically provisions when using `docker-compose.yml`.

---

### 🚨 Alerting (`observability/dashboards/alert_rules.yml`)

Pre-configured Prometheus alert rules:

| Alert | Threshold | Severity |
|-------|-----------|----------|
| **High5xxErrorRate** | > 5% for 2 min | 🔴 Critical |
| **HighRequestLatency** | p95 > 2s for 5 min | 🟡 Warning |
| **ExceptionSpike** | > 1/sec for 2 min | 🟡 Warning |
| **ServiceDown** | Service unreachable | 🔴 Critical |
| **AbnormalRequestRate** | Too high/low | 🟡 Warning |

Configure Slack/PagerDuty notifications in `alertmanager.yml`.

---

### 🔒 CI Enforcement

#### GitHub Actions Workflow (`.github/workflows/observability.yml`)

Runs on every PR to `main`/`develop`:

1. **Observability Check**: Ensures code changes include observability hooks
2. **Linting**: Runs flake8, pylint, mypy on observability module
3. **Auto-Comment**: Comments on PR if observability is missing

**Enforced patterns:**
- ✅ Metrics: `metrics_client`, `Counter`, `Histogram`, `track_function_metrics`
- ✅ Tracing: `start_as_current_span`, `get_tracer()`, `add_span_attributes`
- ✅ Logging: `logger.info`, `logger.error`, `get_logger()`

#### CI Gate Script (`scripts/check_observability_hooks.py`)

```bash
# Run locally to verify your changes
python scripts/check_observability_hooks.py

# Strict mode (requires all 3 categories)
python scripts/check_observability_hooks.py --strict

# Check specific files
python scripts/check_observability_hooks.py --files src/routes/order.py
```

**Exit codes:**
- `0`: Observability hooks found ✅
- `1`: No observability hooks (OBSERVABILITY_MISSING) ❌
- `2`: Script error ⚠️

---

## 📦 Dependencies

All dependencies are in `observability/observability_requirements.txt`:

```txt
prometheus-client>=0.19.0
opentelemetry-api>=1.21.0
opentelemetry-sdk>=1.21.0
opentelemetry-instrumentation-flask>=0.42b0
opentelemetry-instrumentation-requests>=0.42b0
opentelemetry-instrumentation-sqlalchemy>=0.42b0
opentelemetry-exporter-otlp-proto-grpc>=1.21.0
```

---

## 🧪 Testing the Setup

### Generate Test Traffic

```bash
# Install hey (HTTP load generator)
brew install hey  # macOS
# or: go install github.com/rakyll/hey@latest

# Generate 1000 requests
hey -n 1000 -c 10 http://localhost:8000/api/health
```

### Verify Metrics

```bash
curl http://localhost:8000/metrics | grep http_requests_total
```

### Check Traces in Jaeger

1. Open http://localhost:16686
2. Select service: `magsasa-card-erp`
3. Click "Find Traces"
4. View distributed traces with span details

### View Logs

```bash
# Structured JSON logs with trace context
python src/main.py | jq '.'
```

---

## 🔧 Configuration

### Environment Variables

```bash
# OpenTelemetry
export OTEL_SERVICE_NAME=magsasa-card-erp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export OTEL_CONSOLE_EXPORT=false  # Set true to see traces in console
export ENVIRONMENT=development

# Application
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8000
```

### Production Configuration

For production, update `observability/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'magsasa-card-erp'
    static_configs:
      - targets: ['production-api.example.com:8000']
        labels:
          environment: 'production'
```

And point to a production OTLP collector (e.g., Grafana Tempo, Datadog, etc.).

---

## 📊 Integration Examples

### Example 1: Instrumented Route

```python
from flask import Blueprint
from observability.tracing.otel_tracer import get_tracer
from observability.logging.structured_logger import get_logger

order_bp = Blueprint('order', __name__)
tracer = get_tracer(__name__)
logger = get_logger(__name__)

@order_bp.route('/api/orders', methods=['POST'])
def create_order():
    with tracer.start_as_current_span("create_order"):
        logger.info("Order creation started", user_id=current_user.id)
        
        # Business logic
        order = Order(...)
        db.session.add(order)
        db.session.commit()
        
        logger.info("Order created successfully", order_id=order.id, amount=order.total)
        return {"order_id": order.id}, 201
```

### Example 2: Custom Business Metrics

```python
from prometheus_client import Counter, Gauge

orders_created = Counter('orders_created_total', 'Total orders created', ['status'])
active_orders = Gauge('active_orders', 'Number of active orders')

@order_bp.route('/api/orders', methods=['POST'])
def create_order():
    with tracer.start_as_current_span("create_order"):
        try:
            order = create_order_logic()
            orders_created.labels(status='success').inc()
            active_orders.inc()
            return {"order_id": order.id}, 201
        except Exception as e:
            orders_created.labels(status='error').inc()
            logger.error("Order creation failed", error=str(e))
            raise
```

---

## ✅ Verification Checklist

- [x] Metrics middleware installed and `/metrics` endpoint accessible
- [x] OpenTelemetry tracing initialized with OTLP export
- [x] Structured logging configured with JSON output
- [x] Grafana dashboard provisioned and accessible
- [x] Prometheus scraping application metrics
- [x] Jaeger receiving and displaying traces
- [x] Alert rules loaded in Prometheus
- [x] CI workflow enforcing observability hooks
- [x] Application routes instrumented with tracing and logging
- [x] Documentation and quick start guide created

---

## 🎓 Best Practices

### 1. **Always Use Structured Logging**

✅ **DO:**
```python
logger.info("Payment processed", order_id=order.id, amount=amount, currency="PHP")
```

❌ **DON'T:**
```python
logger.info(f"Payment processed: {order.id}, {amount} PHP")
```

### 2. **Trace Critical Paths**

Wrap important business operations in spans:

```python
with tracer.start_as_current_span("process_payment"):
    validate_payment(payment)
    charge_customer(payment)
    send_confirmation(payment)
```

### 3. **Track Business KPIs**

Create custom metrics for business-specific KPIs:

```python
revenue_total = Counter('revenue_total_php', 'Total revenue in PHP')
loan_approvals = Counter('loan_approvals_total', 'Total loan approvals', ['status'])
```

### 4. **Use CI Gate**

Run the observability check locally before pushing:

```bash
python scripts/check_observability_hooks.py
```

---

## 🚀 Next Steps (Stage 6.8)

Consider adding:

1. **Advanced Alerting**: Integrate Slack/PagerDuty for critical alerts
2. **SLO Dashboards**: Define and track Service Level Objectives
3. **Log Aggregation**: Ship logs to ELK/Loki for centralized analysis
4. **APM Integration**: Connect to Datadog/New Relic for advanced APM
5. **Custom Business Dashboards**: Create domain-specific dashboards

---

## 📚 Resources

- [Full Documentation](observability/README.md)
- [Quick Start Guide](observability/QUICKSTART.md)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Grafana Dashboards](https://grafana.com/docs/grafana/latest/dashboards/)

---

## 🎉 Summary

**STAGE 6.7 delivers:**

✅ Production-ready observability framework  
✅ Automatic metrics, tracing, and structured logging  
✅ Complete local dev stack (Prometheus + Grafana + Jaeger)  
✅ CI gate enforcing observability best practices  
✅ Pre-built dashboards and alert rules  
✅ Comprehensive documentation and examples  

**Your team can now:**

- 📊 Monitor service health in real-time
- 🧭 Trace requests across the entire system
- 🔍 Debug issues with correlated logs and traces
- 🚨 Get alerted before users notice problems
- 📈 Track business KPIs alongside technical metrics

---

**🎯 Observability is no longer optional — it's built into your development workflow!**

---

*Generated: October 3, 2025*  
*Stage: 6.7 - Observability & CI Enforcement*  
*Status: ✅ Complete and Production-Ready*

