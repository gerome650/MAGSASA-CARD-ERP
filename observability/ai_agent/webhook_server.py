#!/usr/bin/env python3
"""
Webhook Server for AI Incident Insight Agent

Receives Alertmanager webhooks and triggers incident analysis.
Provides HTTP API endpoints for incident management.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from main import AgentConfig, AIIncidentAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="AI Incident Insight Agent API",
    description="Intelligent incident analysis and response system",
    version="1.0.0",
)

# Global agent instance
agent: AIIncidentAgent | None = None


# Pydantic models
class AlertPayload(BaseModel):
    alerts: list
    groupLabels: dict[str, str]
    commonLabels: dict[str, str]
    commonAnnotations: dict[str, str]
    externalURL: str
    version: str
    groupKey: str


class IncidentRequest(BaseModel):
    incident_id: str
    alert_payload: AlertPayload
    resolution_notes: str | None = None
    engineer_notes: str | None = None


class AnalysisResponse(BaseModel):
    incident_id: str
    status: str
    confidence_score: float
    business_impact: str
    root_causes_count: int
    remediation_actions_count: int
    postmortem_path: str | None = None


@app.on_event("startup")
async def startup_event(_):
    """Initialize the agent on startup"""
    global agent

    logger.info("Starting AI Incident Insight Agent webhook server")

    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.warning("Configuration file not found, using defaults")
        config = AgentConfig()
    else:
        import yaml

        with open(config_path) as f:
            config_data = yaml.safe_load(f)

        config = AgentConfig(
            prometheus_url=config_data.get("data_sources", {})
            .get("prometheus", {})
            .get("base_url", "http://localhost:9090"),
            jaeger_url=config_data.get("data_sources", {})
            .get("jaeger", {})
            .get("base_url", "http://localhost:16686"),
            loki_url=config_data.get("data_sources", {})
            .get("loki", {})
            .get("base_url", "http://localhost:3100"),
            slack_bot_token=config_data.get("notifications", {})
            .get("slack", {})
            .get("bot_token"),
            slack_channels=config_data.get("notifications", {})
            .get("slack", {})
            .get("channels", {}),
            pagerduty_token=config_data.get("notifications", {})
            .get("pagerduty", {})
            .get("api_token"),
            pagerduty_integration_keys=config_data.get("notifications", {})
            .get("pagerduty", {})
            .get("integration_keys", {}),
            reports_dir=config_data.get("postmortem", {}).get(
                "reports_directory", "/observability/reports"
            ),
            analysis_window_minutes=config_data.get("analysis", {}).get(
                "window_minutes", 30
            ),
            confidence_threshold=config_data.get("analysis", {}).get(
                "confidence_threshold", 0.3
            ),
        )

    agent = AIIncidentAgent(config)
    logger.info("AI Incident Agent initialized successfully")


@app.on_event("shutdown")
async def shutdown_event(_):
    """Cleanup on shutdown"""
    logger.info("Shutting down AI Incident Insight Agent webhook server")


@app.get("/health")
async def health_check(_):
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "agent_initialized": agent is not None,
    }


@app.get("/metrics")
async def metrics(_):
    """Prometheus metrics endpoint"""
    # In a real implementation, this would return Prometheus metrics
    return {
        "incidents_analyzed_total": 0,
        "analysis_duration_seconds": 0.0,
        "confidence_score": 0.0,
        "notifications_sent_total": 0,
    }


@app.post("/webhook/alertmanager", response_model=AnalysisResponse)
async def alertmanager_webhook(_alert_payload: AlertPayload, _background_tasks: BackgroundTasks, _request: Request):
    """
    Handle Alertmanager webhook

    Receives alerts from Prometheus Alertmanager and triggers incident analysis
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Generate incident ID
        incident_id = f"INC-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"

        logger.info(f"Received Alertmanager webhook for incident {incident_id}")

        # Convert to dict for analysis
        alert_dict = alert_payload.dict()

        # Run analysis in background
        background_tasks.add_task(analyze_incident_background, incident_id, alert_dict)

        # Return immediate response
        return AnalysisResponse(
            incident_id=incident_id,
            status="analysis_started",
            confidence_score=0.0,
            business_impact="unknown",
            root_causes_count=0,
            remediation_actions_count=0,
        )

    except Exception as e:
        logger.error(f"Error processing Alertmanager webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/api/incidents/{incident_id}/analyze", response_model=AnalysisResponse)
async def analyze_incident(_incident_id: str, _request: IncidentRequest, _background_tasks: BackgroundTasks):
    """
    Analyze a specific incident

    Manually trigger incident analysis with custom parameters
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        logger.info(f"Manual incident analysis requested for {incident_id}")

        # Run analysis in background
        background_tasks.add_task(
            analyze_incident_background,
            incident_id,
            request.alert_payload.dict(),
            request.resolution_notes,
            request.engineer_notes,
        )

        return AnalysisResponse(
            incident_id=incident_id,
            status="analysis_started",
            confidence_score=0.0,
            business_impact="unknown",
            root_causes_count=0,
            remediation_actions_count=0,
        )

    except Exception as e:
        logger.error(f"Error analyzing incident {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.get("/api/incidents/{incident_id}/status")
async def get_incident_status(_incident_id: str):
    """
    Get incident analysis status

    Check the status of incident analysis
    """
    # In a real implementation, this would check the status from a database
    return {
        "incident_id": incident_id,
        "status": "completed",
        "timestamp": datetime.now().isoformat(),
        "message": "Analysis completed successfully",
    }


@app.get("/api/incidents/{incident_id}/postmortem")
async def get_postmortem(_incident_id: str):
    """
    Get postmortem report for an incident

    Retrieve the generated postmortem report
    """
    if not agent:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        # Generate postmortem file path
        incident_date = datetime.now().strftime("%Y-%m-%d")
        postmortem_path = (
            Path(agent.config.reports_dir)
            / f"{incident_date}-incident-{incident_id}.md"
        )

        if not postmortem_path.exists():
            raise HTTPException(status_code=404, detail="Postmortem not found")

        # Read postmortem content
        with open(postmortem_path) as f:
            content = f.read()

        return {
            "incident_id": incident_id,
            "postmortem_path": str(postmortem_path),
            "content": content,
            "generated_at": datetime.now().isoformat(),
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Postmortem not found") from None
    except Exception as e:
        logger.error(f"Error retrieving postmortem for {incident_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from None


@app.post("/api/slack/command")
async def slack_command(_request: Request):
    """
    Handle Slack slash commands

    Process incoming Slack slash commands
    """
    if not agent or not agent.slack_bot:
        raise HTTPException(status_code=503, detail="Slack integration not configured")

    try:
        # Parse form data from Slack
        form_data = await request.form()
        command_data = dict(form_data)

        logger.info(f"Received Slack command: {command_data.get('command')}")

        # Handle command
        response = await agent.slack_bot.handle_command(command_data)

        return JSONResponse(content={"text": response})

    except Exception as e:
        logger.error(f"Error handling Slack command: {e}")
        return JSONResponse(
            status_code=500, content={"text": f"❌ Error processing command: {str(e)}"}
        )


@app.post("/api/slack/interactive")
async def slack_interactive(_request: Request):
    """
    Handle Slack interactive messages

    Process interactive Slack message interactions (buttons, selects)
    """
    if not agent or not agent.slack_bot:
        raise HTTPException(status_code=503, detail="Slack integration not configured")

    try:
        # Parse form data from Slack
        form_data = await request.form()
        payload = json.loads(form_data.get("payload", "{}"))

        logger.info(f"Received Slack interactive message: {payload.get('type')}")

        # Handle interaction
        response = await agent.slack_bot.handle_interactive_message(payload)

        return JSONResponse(content={"text": response})

    except Exception as e:
        logger.error(f"Error handling Slack interactive message: {e}")
        return JSONResponse(
            status_code=500,
            content={"text": f"❌ Error processing interaction: {str(e)}"},
        )


async def analyze_incident_background(_incident_id: str, _alert_payload: dict[str, _Any], resolution_notes: str | None = None, engineer_notes: str | None = None, _):
    """Run incident analysis in background"""
    try:
        logger.info(f"Starting background analysis for incident {incident_id}")

        if not agent:
            logger.error("Agent not initialized for background analysis")
            return

        # Run analysis
        results = await agent.analyze_incident(
            incident_id=incident_id,
            alert_payload=alert_payload,
            resolution_notes=resolution_notes,
            engineer_notes=engineer_notes,
        )

        logger.info(f"Background analysis completed for incident {incident_id}")

        # Log results summary
        insight = results["insight"]
        logger.info(
            f"Incident {incident_id} - Impact: {insight['business_impact']}, "
            f"Confidence: {insight['confidence_score']:.1%}, "
            f"Root Causes: {len(results['root_causes'])}"
        )

    except Exception as e:
        logger.error(f"Error in background analysis for incident {incident_id}: {e}")


def main(_):
    """Main function to run the webhook server"""
    import argparse

    parser = argparse.ArgumentParser(
        description="AI Incident Insight Agent Webhook Server"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8080, help="Port to bind to")
    parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes"
    )
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload for development"
    )

    args = parser.parse_args()

    logger.info(f"Starting webhook server on {args.host}:{args.port}")

    uvicorn.run(
        "webhook_server:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        reload=args.reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
