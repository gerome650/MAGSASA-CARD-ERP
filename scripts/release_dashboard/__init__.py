"""
Release Dashboard Updater - Modular Package

This package provides modular components for updating the release readiness dashboard.
"""

from .fetch import GitHubWorkflowFetcher
from .notify import SlackNotifier
from .scoring import ReadinessScorer
from .update import MarkdownUpdater

__all__ = [
    "GitHubWorkflowFetcher",
    "MarkdownUpdater",
    "SlackNotifier",
    "ReadinessScorer",
]

__version__ = "1.0.0"
