# 🤖 AI Incident Insight Agent

An intelligent incident analysis and response system that transforms raw alerts into actionable insights, automated remediation recommendations, and comprehensive postmortem reports.

## 🎯 Overview

The AI Incident Insight Agent is a production-ready system that:

- 📊 **Correlates** metrics, logs, traces, alerts, and deployments to detect root causes
- 🧠 **Analyzes** incidents using machine learning patterns and historical data
- 📝 **Generates** natural-language summaries and remediation recommendations
- 💬 **Integrates** with Slack and PagerDuty for real-time notifications
- 📚 **Creates** automated postmortem reports for knowledge sharing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   AI Agent      │    │   Outputs       │
│                 │    │                 │    │                 │
│ • Prometheus    │───▶│ • Data Collector│───▶│ • Slack Reports │
│ • Jaeger        │    │ • Incident      │    │ • PagerDuty     │
│ • Loki/ELK      │    │   Analyzer      │    │ • Postmortems   │
│ • GitHub        │    │ • Insight       │    │ • Dashboards    │
│ • Alertmanager  │    │   Engine        │    │ • Runbooks      │
└─────────────────┘    │ • Remediation   │    └─────────────────┘
                       │   Advisor       │
                       │ • Postmortem    │
                       │   Generator     │
                       └─────────────────┘
```

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r observability/ai_agent/requirements.txt

# Set up environment variables
export SLACK_BOT_TOKEN="xoxb-your-slack-token"
export PAGERDUTY_TOKEN="your-pagerduty-token"
export GITHUB_TOKEN="your-github-token"
```

### 2. Configuration

Copy and customize the configuration file:

```bash
cp observability/ai_agent/config.yaml.example observability/ai_agent/config.yaml
```

Edit `config.yaml` to match your environment:

```yaml
data_sources:
  prometheus:
    base_url: "http://your-prometheus:9090"
  jaeger:
    base_url: "http://your-jaeger:16686"

notifications:
  slack:
    enabled: true
    bot_token: "${SLACK_BOT_TOKEN}"
    channels:
      incidents: "#incident-response"
```

### 3. Run Analysis

```bash
# Analyze an incident
python -m observability.ai_agent.cli analyze \
  --incident-id INC-2025-01-03-001 \
  --service magsasa-card-erp \
  --severity critical \
  --summary "High latency detected"

# Run tests
python -m observability.ai_agent.cli test --scenarios --integration

# Generate postmortem
python -m observability.ai_agent.cli postmortem \
  --incident-id INC-2025-01-03-001 \
  --incident-file incident_data.json
```

## 📁 Project Structure

```
observability/ai_agent/
├── __init__.py                 # Package initialization
├── main.py                     # Main orchestrator
├── cli.py                      # Command-line interface
├── config.yaml                 # Configuration file
├── README.md                   # This file
│
├── data_collector.py           # Telemetry data aggregation
├── incident_analyzer.py        # Root cause analysis
├── insight_engine.py           # Narrative generation
├── remediation_advisor.py      # Action recommendations
├── incident_reporter.py        # Report formatting
├── postmortem_generator.py     # Postmortem creation
│
├── integrations/
│   ├── __init__.py
│   ├── slack_bot.py            # Slack integration
│   └── pagerduty_notifier.py   # PagerDuty integration
│
└── test_workflow.py            # Testing and validation
```

## 🔧 Components

### Data Collector (`data_collector.py`)

Aggregates telemetry from all sources:

- **Metrics**: Prometheus queries for anomalies
- **Logs**: Loki/ELK pattern analysis
- **Traces**: Jaeger span analysis
- **Deployments**: GitHub commit correlation
- **System Events**: Infrastructure monitoring

```python
from observability.ai_agent import IncidentContextCollector

collector = IncidentContextCollector(config)
context = await collector.collect_incident_context(
    incident_id="INC-001",
    alert_payload=alert_data,
    window_minutes=30
)
```

### Incident Analyzer (`incident_analyzer.py`)

Correlates anomalies with known root causes:

- **Deployment Regression**: Code changes causing issues
- **Database Issues**: Query performance, connection problems
- **Infrastructure Degradation**: Resource exhaustion, node failures
- **Dependency Failures**: External service outages
- **Resource Exhaustion**: Memory leaks, CPU saturation

```python
from observability.ai_agent import IncidentAnalyzer

analyzer = IncidentAnalyzer()
root_causes = analyzer.analyze_incident(context)
```

### Insight Engine (`insight_engine.py`)

Generates human-readable insights:

- **Summary**: One-paragraph incident description
- **Timeline**: Chronological event sequence
- **Impact Analysis**: User and service impact assessment
- **Next Steps**: Immediate recommended actions

```python
from observability.ai_agent import InsightEngine

engine = InsightEngine()
insight = engine.generate_insight(context, root_causes)
```

### Remediation Advisor (`remediation_advisor.py`)

Suggests specific remediation actions:

- **Rollback**: Deployment rollback procedures
- **Scaling**: Resource scaling recommendations
- **Configuration**: Config fixes and optimizations
- **Monitoring**: Enhanced monitoring setup

```python
from observability.ai_agent import RemediationAdvisor

advisor = RemediationAdvisor()
actions = advisor.generate_remediation_plan(insight)
```

### Postmortem Generator (`postmortem_generator.py`)

Creates comprehensive postmortem reports:

- **Executive Summary**: High-level incident overview
- **Timeline**: Detailed event chronology
- **Root Cause Analysis**: Technical investigation results
- **Impact Assessment**: Business and user impact
- **Lessons Learned**: Key takeaways and improvements
- **Action Items**: Follow-up tasks and improvements

```python
from observability.ai_agent import PostmortemGenerator

generator = PostmortemGenerator("/observability/reports")
postmortem = generator.generate_postmortem(
    insight, 
    actions,
    resolution_notes="Rolled back deployment",
    engineer_notes="Team responded quickly"
)
```

## 🔌 Integrations

### Slack Integration

Interactive Slack bot with slash commands:

```bash
/incident list                    # List recent incidents
/incident details INC-001        # Get incident details
/incident-summary INC-001        # Get incident summary
/postmortem INC-001              # Generate postmortem
```

### PagerDuty Integration

Automatic incident creation and management:

- **Incident Creation**: Auto-creates PagerDuty incidents
- **Severity Mapping**: Maps business impact to PagerDuty severity
- **Rich Context**: Includes root causes and remediation steps
- **Auto-Resolution**: Resolves incidents when fixed

## 📊 Example Output

### Incident Summary

```
🚨 Incident Report: INC-2025-01-03-001

Summary:
At 14:32 UTC, p95 latency increased by 240% following deployment v1.4.2. 
Error rates spiked to 7% due to database query timeouts. The incident 
lasted 45 minutes and affected 3 services: magsasa-card-erp, payment-service, order-service.

Impact Analysis:
• Business Impact: High
• Users Affected: 1,200
• Duration: 45 minutes
• Confidence: 87%

Root Causes:
1. Deployment Regression (87% confidence)
   - Inefficient ORM query introduced in PR #812
   - Database connection timeout errors detected

Immediate Actions Required:
• Rollback deployment to v1.4.1 (10 minutes)
• Check database connection pool settings (15 minutes)
• Review slow query logs (20 minutes)
```

### Postmortem Report

```markdown
# 🧠 Incident Postmortem – INC-2025-01-03-001

## Summary
Database query timeout caused error rates to spike to 7% following deployment v1.4.2.

## Timeline
- 14:32 UTC – Deployment v1.4.2 released
- 14:34 UTC – Latency anomaly detected
- 14:36 UTC – Alerts fired to Slack
- 14:45 UTC – Rollback initiated
- 14:55 UTC – Latency normalized

## Root Causes
1. N+1 query pattern in orders_repository.py (confidence: 0.88)

## Impact
- 18% of user requests affected
- 12-minute SLA breach window
- Estimated 240 failed transactions

## Lessons Learned
- Introduce automated query regression tests
- Add traffic replay stage to staging environment
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python -m observability.ai_agent.cli test --scenarios --integration

# Run specific test scenarios
python -m observability.ai_agent.cli test --scenarios

# Run integration tests
python -m observability.ai_agent.cli test --integration
```

Test scenarios include:
- Deployment regression detection
- Database issue analysis
- Infrastructure degradation
- Dependency failure handling
- Resource exhaustion scenarios

## 📈 Monitoring

The agent exposes Prometheus metrics:

- `ai_agent_incidents_analyzed_total` - Total incidents analyzed
- `ai_agent_analysis_duration_seconds` - Analysis time
- `ai_agent_confidence_score` - Analysis confidence
- `ai_agent_notifications_sent_total` - Notifications sent

## 🔒 Security

- **Authentication**: Uses OAuth tokens for all integrations
- **Authorization**: Role-based access control
- **Encryption**: All communications use TLS
- **Rate Limiting**: Prevents abuse and DoS attacks

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY observability/ai_agent/ .
RUN pip install -r requirements.txt

CMD ["python", "-m", "observability.ai_agent.cli", "analyze"]
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ai-incident-agent
spec:
  replicas: 2
  selector:
    matchLabels:
      app: ai-incident-agent
  template:
    metadata:
      labels:
        app: ai-incident-agent
    spec:
      containers:
      - name: ai-agent
        image: magsasa/ai-incident-agent:latest
        env:
        - name: SLACK_BOT_TOKEN
          valueFrom:
            secretKeyRef:
              name: ai-agent-secrets
              key: slack-bot-token
```

## 📚 API Reference

### Main Agent

```python
from observability.ai_agent import AIIncidentAgent, AgentConfig

# Initialize agent
config = AgentConfig(
    prometheus_url="http://localhost:9090",
    slack_bot_token="xoxb-...",
    pagerduty_token="..."
)

agent = AIIncidentAgent(config)

# Analyze incident
results = await agent.analyze_incident(
    incident_id="INC-001",
    alert_payload=alert_data,
    resolution_notes="Fixed by rollback",
    engineer_notes="Need better testing"
)
```

### Individual Components

```python
# Data collection
collector = IncidentContextCollector(config)
context = await collector.collect_incident_context(...)

# Analysis
analyzer = IncidentAnalyzer()
root_causes = analyzer.analyze_incident(context)

# Insights
engine = InsightEngine()
insight = engine.generate_insight(context, root_causes)

# Remediation
advisor = RemediationAdvisor()
actions = advisor.generate_remediation_plan(insight)

# Postmortem
generator = PostmortemGenerator()
postmortem = generator.generate_postmortem(insight, actions)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/magsasa/ai-incident-agent/wiki)
- **Issues**: [GitHub Issues](https://github.com/magsasa/ai-incident-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/magsasa/ai-incident-agent/discussions)
- **Email**: incident-response@magsasa.com

---

**Built with ❤️ by the MAGSASA Engineering Team**
