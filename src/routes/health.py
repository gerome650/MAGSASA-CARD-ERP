#!/usr/bin/env python3
"""
Health Check Endpoint - Stage 6.5
Provides service health and readiness checks for chaos engineering tests.
"""

import time
from datetime import datetime
from flask import Blueprint, jsonify
from src.database import db

health_bp = Blueprint('health', __name__)


@health_bp.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for service monitoring and chaos engineering.

    Returns:
        JSON response with health status, timestamp, and basic system info
    """
    start_time = time.time()

    try:
        # Check database connectivity
        db_healthy = True
        db_error = None
        try:
            # Simple query to test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
        except Exception as e:
            db_healthy = False
            db_error = str(e)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Determine overall health status
        healthy = db_healthy
        status = "healthy" if healthy else "unhealthy"

        response = {
            "status": status,
            "healthy": healthy,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": round(response_time_ms, 2),
            "checks": {
                "database": {
                    "healthy": db_healthy,
                    "error": db_error
                }
            },
            "service": {
                "name": "MAGSASA-CARD-ERP",
                "version": "6.5.0",
                "environment": "development"
            }
        }

        # Return appropriate HTTP status code
        status_code = 200 if healthy else 503
        return jsonify(response), status_code

    except Exception as e:
        # Fallback error response
        response = {
            "status": "error",
            "healthy": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "service": {
                "name": "MAGSASA-CARD-ERP",
                "version": "6.5.0",
                "environment": "development"
            }
        }
        return jsonify(response), 500


@health_bp.route('/api/health/ready', methods=['GET'])
def readiness_check():
    """
    Readiness check endpoint - more comprehensive than health check.

    Returns:
        JSON response indicating if service is ready to accept traffic
    """
    start_time = time.time()

    try:
        checks = {}
        all_ready = True

        # Database readiness
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            checks["database"] = {"ready": True, "message": "Database connection successful"}
        except Exception as e:
            checks["database"] = {"ready": False, "message": f"Database error: {str(e)}"}
            all_ready = False

        # Add more readiness checks here as needed
        # For example: external API dependencies, file system access, etc.

        response_time_ms = (time.time() - start_time) * 1000

        response = {
            "ready": all_ready,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": round(response_time_ms, 2),
            "checks": checks,
            "service": {
                "name": "MAGSASA-CARD-ERP",
                "version": "6.5.0",
                "environment": "development"
            }
        }

        status_code = 200 if all_ready else 503
        return jsonify(response), status_code

    except Exception as e:
        response = {
            "ready": False,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "error": str(e),
            "service": {
                "name": "MAGSASA-CARD-ERP",
                "version": "6.5.0",
                "environment": "development"
            }
        }
        return jsonify(response), 500


@health_bp.route('/api/health/live', methods=['GET'])
def liveness_check():
    """
    Liveness check endpoint - minimal check to verify service is alive.

    Returns:
        Simple JSON response indicating service is alive
    """
    return jsonify({
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": "MAGSASA-CARD-ERP"
    }), 200
