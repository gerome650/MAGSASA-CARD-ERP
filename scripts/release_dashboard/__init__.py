"""
Release Dashboard Updater - Modular Package

This package provides modular components for updating the release readiness dashboard.
"""

from .fetch import GitHubWorkflowFetcher
from .update import MarkdownUpdater
from .notify import SlackNotifier
from .scoring import ReadinessScorer

__all__ = [
    'GitHubWorkflowFetcher',
    'MarkdownUpdater',
    'SlackNotifier',
    'ReadinessScorer'
]

__version__ = '1.0.0'

