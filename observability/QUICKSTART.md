# 🚀 Observability Quick Start Guide

Get the complete observability stack running in under 5 minutes!

## 📦 Prerequisites

- Docker and Docker Compose installed
- Python 3.8+ with pip

## 🏃 Quick Start

### 1. Start the Observability Stack

```bash
cd observability/
docker-compose up -d
```

This starts:
- **Prometheus** (metrics) → http://localhost:9090
- **Grafana** (dashboards) → http://localhost:3000
- **Jaeger** (tracing) → http://localhost:16686
- **Alertmanager** (alerts) → http://localhost:9093

### 2. Install Python Dependencies

```bash
pip install -r observability_requirements.txt
```

Or manually:

```bash
pip install prometheus-client opentelemetry-api opentelemetry-sdk \
    opentelemetry-instrumentation-flask opentelemetry-instrumentation-requests \
    opentelemetry-instrumentation-sqlalchemy opentelemetry-exporter-otlp-proto-grpc
```

### 3. Instrument Your Flask App

Edit `src/main.py`:

```python
from observability.metrics.metrics_middleware import MetricsMiddleware
from observability.tracing.otel_tracer import init_tracing
from observability.logging.structured_logger import configure_root_logger

app = Flask(__name__)

# Enable observability
MetricsMiddleware(app)
init_tracing(app, otlp_endpoint="http://localhost:4317", console_export=False)
configure_root_logger()

# Your app code...
```

### 4. Start Your Application

```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8000
python src/main.py
```

### 5. Access the Dashboards

#### Grafana (Visualization)
- URL: http://localhost:3000
- Username: `admin`
- Password: `admin`
- Dashboard: Navigate to "MAGSASA-CARD-ERP Service Dashboard"

#### Prometheus (Metrics)
- URL: http://localhost:9090
- Query examples:
  - `rate(http_requests_total[5m])` - Request rate
  - `http_request_duration_seconds` - Latency

#### Jaeger (Tracing)
- URL: http://localhost:16686
- Service: `magsasa-card-erp`
- View traces and spans for distributed tracing

## 🧪 Test the Setup

### Generate Test Traffic

```bash
# Install hey (HTTP load generator)
# Mac: brew install hey
# Linux: go install github.com/rakyll/hey@latest

# Generate load
hey -n 1000 -c 10 http://localhost:8000/api/health
```

### Check Metrics

```bash
curl http://localhost:8000/metrics
```

You should see Prometheus metrics like:
```
http_requests_total{endpoint="/api/health",method="GET",status_code="200"} 1000
http_request_duration_seconds_count{endpoint="/api/health",method="GET"} 1000
```

### View in Grafana

1. Go to http://localhost:3000
2. Login (admin/admin)
3. Navigate to Dashboards → MAGSASA-CARD-ERP Service Dashboard
4. See real-time metrics!

## 📊 What You Get

### Metrics (Prometheus)
- ✅ Request rates (QPS)
- ✅ Request latency (p50, p95, p99)
- ✅ Error rates (4xx, 5xx)
- ✅ Exception tracking
- ✅ Custom business metrics

### Tracing (Jaeger)
- ✅ Distributed traces across services
- ✅ Request flow visualization
- ✅ Performance bottleneck identification
- ✅ Trace-to-log correlation

### Logging (Structured JSON)
- ✅ JSON-formatted logs
- ✅ Automatic trace context injection
- ✅ Structured fields for querying
- ✅ Easy integration with log aggregators

### Dashboards (Grafana)
- ✅ Service health overview
- ✅ Request rate and latency
- ✅ Error tracking
- ✅ Top endpoints by traffic
- ✅ Custom visualizations

### Alerts (Alertmanager)
- ✅ High error rate alerts
- ✅ Latency anomaly detection
- ✅ Service downtime alerts
- ✅ Exception spike detection

## 🛠️ Configuration

### Environment Variables

```bash
# OpenTelemetry configuration
export OTEL_SERVICE_NAME=magsasa-card-erp
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317
export ENVIRONMENT=development

# Application configuration
export FLASK_HOST=0.0.0.0
export FLASK_PORT=8000
```

### Docker Compose Overrides

Create `docker-compose.override.yml` for custom configuration:

```yaml
version: '3.8'

services:
  prometheus:
    ports:
      - "9091:9090"  # Custom port
  
  grafana:
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=your-secure-password
```

## 🔧 Troubleshooting

### Metrics not appearing in Prometheus

1. Check if your app is accessible from Docker:
   ```bash
   docker exec magsasa-prometheus wget -O- http://host.docker.internal:8000/metrics
   ```

2. For Linux, update `prometheus.yml`:
   ```yaml
   - targets: ['172.17.0.1:8000']  # Replace with your bridge IP
   ```

### Traces not appearing in Jaeger

1. Verify OTLP endpoint is configured:
   ```python
   init_tracing(app, otlp_endpoint="http://localhost:4317")
   ```

2. Check Jaeger is receiving spans:
   ```bash
   docker logs magsasa-jaeger
   ```

### Grafana dashboard is empty

1. Wait 15-30 seconds for Prometheus to scrape metrics
2. Verify Prometheus data source is configured:
   - Go to Configuration → Data Sources
   - Check "Prometheus" is set as default
   - Test connection

### Port conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
services:
  grafana:
    ports:
      - "3001:3000"  # Use port 3001 instead
```

## 📚 Next Steps

1. **Customize Dashboards**: Edit `dashboards/service_dashboard.json`
2. **Add Custom Metrics**: See `observability/README.md`
3. **Configure Alerts**: Edit `dashboards/alert_rules.yml`
4. **Set up Slack Alerts**: Configure `alertmanager.yml`
5. **Add Business KPIs**: Create custom metrics for your domain

## 🧹 Cleanup

Stop and remove all containers:

```bash
cd observability/
docker-compose down -v
```

This removes containers and volumes (data will be lost).

To keep data, omit `-v`:

```bash
docker-compose down
```

## 📖 Resources

- [Full Documentation](README.md)
- [CI/CD Integration](.github/workflows/observability.yml)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Jaeger Docs](https://www.jaegertracing.io/docs/)

## 💡 Tips

- **Development**: Use `console_export=True` in `init_tracing()` to see traces in console
- **Production**: Point to production OTLP collector (Tempo, Jaeger, etc.)
- **Performance**: Adjust scrape intervals in `prometheus.yml` for production
- **Alerts**: Configure Slack/PagerDuty webhooks in `alertmanager.yml`

---

🎉 **You're all set!** Your application now has production-grade observability.

