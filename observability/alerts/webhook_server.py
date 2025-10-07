"""
Runtime Intelligence: Webhook Server for Alert Integration
Stage 6.8 - Central webhook server that integrates all runtime intelligence components

This server receives alerts from Alertmanager and orchestrates:
- Smart alert routing via notifier.py
- Dashboard annotations via annotations.py
- Runtime intelligence processing
"""

import logging
import os
import signal
import sys
import threading
import time
from datetime import datetime
from typing import Any

from flask import Flask, jsonify, request

from ..dashboards.annotations import annotate_alert, annotation_manager

# Import our runtime intelligence components
from .anomaly_strategies import runtime_intelligence
from .notifier import route_alert

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global state
webhook_stats = {
    "total_alerts": 0,
    "successful_routes": 0,
    "failed_routes": 0,
    "annotations_created": 0,
    "start_time": datetime.now(),
}

# Alert suppression cache
alert_suppression = {}
suppression_lock = threading.Lock()


def should_suppress_alert(alert_data: dict[str, Any]) -> bool:
    """
    Check if alert should be suppressed to prevent spam.

    Args:
        alert_data: Alert data from Alertmanager

    Returns:
        True if alert should be suppressed
    """
    labels = alert_data.get("labels", {})
    alertname = labels.get("alertname", "unknown")
    severity = labels.get("severity", "info")
    service = labels.get("service", "unknown")

    # Create suppression key
    suppression_key = f"{service}:{alertname}:{severity}"

    with suppression_lock:
        current_time = time.time()

        # Check if alert is already suppressed
        if suppression_key in alert_suppression:
            suppress_until = alert_suppression[suppression_key]
            if current_time < suppress_until:
                return True

        # Set suppression based on severity
        suppress_duration = {
            "critical": 600,  # 10 minutes
            "warning": 300,  # 5 minutes
            "info": 180,  # 3 minutes
        }.get(severity, 180)

        alert_suppression[suppression_key] = current_time + suppress_duration
        return False


def process_alert(alert_data: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single alert through the runtime intelligence pipeline.

    Args:
        alert_data: Alert data from Alertmanager

    Returns:
        Processing result dictionary
    """
    result = {
        "alert_processed": False,
        "routing_success": False,
        "annotation_created": False,
        "anomaly_detected": False,
        "error": None,
    }

    try:
        labels = alert_data.get("labels", {})
        alertname = labels.get("alertname", "unknown")
        severity = labels.get("severity", "info")

        logger.info(f"Processing alert: {alertname} (severity: {severity})")

        # Check suppression
        if should_suppress_alert(alert_data):
            logger.info(f"Alert suppressed: {alertname}")
            result["alert_processed"] = True
            result["suppressed"] = True
            return result

        # Route alert to appropriate channels
        try:
            routing_result = route_alert(alert_data)
            result["routing_success"] = any(routing_result.values())
            result["routing_details"] = routing_result
            logger.info(f"Alert routed: {routing_result}")
        except Exception as e:
            logger.error(f"Failed to route alert: {e}")
            result["error"] = f"Routing failed: {str(e)}"

        # Create dashboard annotation
        try:
            annotation_success = annotate_alert(alert_data)
            result["annotation_created"] = annotation_success
            if annotation_success:
                webhook_stats["annotations_created"] += 1
            logger.info(f"Annotation created: {annotation_success}")
        except Exception as e:
            logger.error(f"Failed to create annotation: {e}")
            if not result["error"]:
                result["error"] = f"Annotation failed: {str(e)}"

        # Check for ML anomaly detection
        try:
            # This would be called by the anomaly detection service
            # For now, we'll just log that we're checking
            logger.debug(f"Checking for ML anomalies related to {alertname}")
            result["anomaly_detected"] = False  # Placeholder
        except Exception as e:
            logger.error(f"Failed to check anomalies: {e}")

        result["alert_processed"] = True
        webhook_stats["successful_routes"] += 1

    except Exception as e:
        logger.error(f"Error processing alert: {e}")
        result["error"] = str(e)
        webhook_stats["failed_routes"] += 1

    return result


@app.route("/health", methods=["GET"])
def health_check(_):
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "stats": webhook_stats,
        }
    )


@app.route("/webhook", methods=["POST"])
def webhook_default(_):
    """Default webhook endpoint"""
    return handle_webhook(request, "default")


@app.route("/webhook/critical", methods=["POST"])
def webhook_critical(_):
    """Critical alerts webhook"""
    return handle_webhook(request, "critical")


@app.route("/webhook/warning", methods=["POST"])
def webhook_warning(_):
    """Warning alerts webhook"""
    return handle_webhook(request, "warning")


@app.route("/webhook/info", methods=["POST"])
def webhook_info(_):
    """Info alerts webhook"""
    return handle_webhook(request, "info")


@app.route("/webhook/smart-router", methods=["POST"])
def webhook_smart_router(_):
    """Smart router webhook - main processing endpoint"""
    return handle_webhook(request, "smart-router")


@app.route("/webhook/pagerduty", methods=["POST"])
def webhook_pagerduty(_):
    """PagerDuty webhook endpoint"""
    return handle_webhook(request, "pagerduty")


def handle_webhook(_request_obj, _endpoint_type: str):
    """
    Handle incoming webhook requests.

    Args:
        request_obj: Flask request object
        endpoint_type: Type of webhook endpoint

    Returns:
        JSON response
    """
    try:
        # Get request data
        if request_obj.is_json:
            data = request_obj.get_json()
        else:
            data = request_obj.form.to_dict()

        logger.info(
            f"Received {endpoint_type} webhook with {len(data.get('alerts', []))} alerts"
        )

        # Update stats
        webhook_stats["total_alerts"] += len(data.get("alerts", []))

        # Process each alert
        results = []
        alerts = data.get("alerts", [])

        for _alert in alerts:
            alert_result = process_alert(alert)
            results.append(
                {
                    "alertname": alert.get("labels", {}).get("alertname", "unknown"),
                    "result": alert_result,
                }
            )

        # Return success response
        return jsonify(
            {
                "status": "success",
                "processed": len(results),
                "endpoint": endpoint_type,
                "results": results,
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Error handling {endpoint_type} webhook: {e}")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "endpoint": endpoint_type,
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            500,
        )


@app.route("/stats", methods=["GET"])
def get_stats(_):
    """Get webhook processing statistics"""
    uptime = datetime.now() - webhook_stats["start_time"]

    return jsonify(
        {
            "stats": webhook_stats,
            "uptime_seconds": uptime.total_seconds(),
            "suppression_cache_size": len(alert_suppression),
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/suppression/clear", methods=["POST"])
def clear_suppression(_):
    """Clear alert suppression cache"""
    with suppression_lock:
        alert_suppression.clear()

    logger.info("Alert suppression cache cleared")
    return jsonify(
        {
            "status": "success",
            "message": "Suppression cache cleared",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/test", methods=["POST"])
def test_webhook(_):
    """Test webhook with sample alert data"""
    sample_alert = {
        "labels": {
            "alertname": "TestAlert",
            "severity": "warning",
            "service": "magsasa-card-erp",
            "team": "backend",
            "category": "test",
        },
        "annotations": {
            "summary": "Test alert for runtime intelligence",
            "description": "This is a test alert to verify the webhook functionality",
            "current_value": "100",
            "baseline_value": "50",
            "runbook_url": "https://docs.example.com/runbooks/test",
            "grafana_url": "http://grafana:3000/d/test",
        },
        "status": "firing",
        "startsAt": datetime.now().isoformat() + "Z",
    }

    # Process the test alert
    result = process_alert(sample_alert)

    return jsonify(
        {
            "status": "success",
            "test_alert": sample_alert,
            "processing_result": result,
            "timestamp": datetime.now().isoformat(),
        }
    )


def signal_handler(_signum, _frame):
    """Handle shutdown signals gracefully"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)


def start_webhook_server(host="0.0.0.0", port=5001, debug=False):
    """
    Start the webhook server.

    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    logger.info(f"Starting Runtime Intelligence Webhook Server on {host}:{port}")
    logger.info("Available endpoints:")
    logger.info("  POST /webhook - Default webhook")
    logger.info("  POST /webhook/critical - Critical alerts")
    logger.info("  POST /webhook/warning - Warning alerts")
    logger.info("  POST /webhook/info - Info alerts")
    logger.info("  POST /webhook/smart-router - Smart routing")
    logger.info("  POST /webhook/pagerduty - PagerDuty integration")
    logger.info("  GET /health - Health check")
    logger.info("  GET /stats - Statistics")
    logger.info("  POST /test - Test webhook")
    logger.info("  POST /suppression/clear - Clear suppression cache")

    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except KeyboardInterrupt:
        logger.info("Webhook server stopped by user")
    except Exception as e:
        logger.error(f"Webhook server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Initialize components
    try:
        # Initialize annotation manager if not already done
        if annotation_manager is None:
            api_key = os.getenv("GRAFANA_API_KEY", "your-api-key")

            if api_key != "your-api-key":
                from ..dashboards.annotations import initialize_annotation_manager

                initialize_annotation_manager(grafana_url, api_key)
                logger.info("Annotation manager initialized")
            else:
                logger.warning("GRAFANA_API_KEY not set, annotations will be disabled")

        # Start runtime intelligence monitoring
        runtime_intelligence.run_continuous_monitoring()
        logger.info("Runtime intelligence monitoring started")

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")

    # Start webhook server
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "5001"))
    debug = os.getenv("WEBHOOK_DEBUG", "false").lower() == "true"

    start_webhook_server(host=host, port=port, debug=debug)
