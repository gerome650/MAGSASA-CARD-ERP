#!/usr/bin/env python3
"""
Namespace Integrity Tests for observability.ai_agent

This test suite ensures that the ai_agent package properly exposes all submodules
for dynamic imports, mocking, and patching. These tests prevent AttributeError
issues when using unittest.mock.patch or dynamic module resolution.

Purpose:
--------
1. Verify all critical submodules are accessible via observability.ai_agent
2. Prevent namespace regression when refactoring package structure
3. Ensure test mocks can resolve module paths correctly
4. Validate that __all__ exports are complete and accurate

Background:
-----------
The ai_agent package must explicitly import submodules in __init__.py to make
them available for dynamic access. Without this, unittest.mock.patch() calls
like patch("observability.ai_agent.webhook_server.app") will fail with
AttributeError because Python's import system doesn't automatically load
submodules into the parent namespace.
"""

import pytest

import observability.ai_agent as ai_agent


class TestNamespaceExports:
    """Test that all critical modules are exported in the ai_agent namespace"""

    def test_webhook_server_module_exists(self):
        """Ensure webhook_server module is accessible"""
        assert hasattr(ai_agent, "webhook_server"), (
            "webhook_server module not found in ai_agent namespace. "
            "Ensure 'from . import webhook_server' is in __init__.py"
        )

    def test_webhook_server_app_exists(self):
        """Ensure FastAPI app is accessible via webhook_server module"""
        assert hasattr(ai_agent.webhook_server, "app"), (
            "FastAPI app not found in webhook_server module. "
            "This is required for mocking in tests."
        )

    def test_main_module_exists(self):
        """Ensure main module is accessible"""
        assert hasattr(ai_agent, "main"), (
            "main module not found in ai_agent namespace. "
            "Ensure 'from . import main' is in __init__.py"
        )

    def test_cli_module_exists(self):
        """Ensure cli module is accessible"""
        assert hasattr(ai_agent, "cli"), (
            "cli module not found in ai_agent namespace. "
            "Ensure 'from . import cli' is in __init__.py"
        )

    def test_data_collector_module_exists(self):
        """Ensure data_collector module is accessible"""
        assert hasattr(ai_agent, "data_collector"), (
            "data_collector module not found in ai_agent namespace. "
            "Ensure 'from . import data_collector' is in __init__.py"
        )

    def test_incident_analyzer_module_exists(self):
        """Ensure incident_analyzer module is accessible"""
        assert hasattr(ai_agent, "incident_analyzer"), (
            "incident_analyzer module not found in ai_agent namespace. "
            "Ensure 'from . import incident_analyzer' is in __init__.py"
        )

    def test_incident_reporter_module_exists(self):
        """Ensure incident_reporter module is accessible"""
        assert hasattr(ai_agent, "incident_reporter"), (
            "incident_reporter module not found in ai_agent namespace. "
            "Ensure 'from . import incident_reporter' is in __init__.py"
        )

    def test_insight_engine_module_exists(self):
        """Ensure insight_engine module is accessible"""
        assert hasattr(ai_agent, "insight_engine"), (
            "insight_engine module not found in ai_agent namespace. "
            "Ensure 'from . import insight_engine' is in __init__.py"
        )

    def test_postmortem_generator_module_exists(self):
        """Ensure postmortem_generator module is accessible"""
        assert hasattr(ai_agent, "postmortem_generator"), (
            "postmortem_generator module not found in ai_agent namespace. "
            "Ensure 'from . import postmortem_generator' is in __init__.py"
        )

    def test_remediation_advisor_module_exists(self):
        """Ensure remediation_advisor module is accessible"""
        assert hasattr(ai_agent, "remediation_advisor"), (
            "remediation_advisor module not found in ai_agent namespace. "
            "Ensure 'from . import remediation_advisor' is in __init__.py"
        )


class TestClassExports:
    """Test that all classes are exported for backward compatibility"""

    def test_incident_context_collector_class(self):
        """Ensure IncidentContextCollector class is exported"""
        assert hasattr(ai_agent, "IncidentContextCollector"), (
            "IncidentContextCollector class not exported. "
            "Check __all__ list in __init__.py"
        )

    def test_incident_analyzer_class(self):
        """Ensure IncidentAnalyzer class is exported"""
        assert hasattr(ai_agent, "IncidentAnalyzer"), (
            "IncidentAnalyzer class not exported. " "Check __all__ list in __init__.py"
        )

    def test_insight_engine_class(self):
        """Ensure InsightEngine class is exported"""
        assert hasattr(ai_agent, "InsightEngine"), (
            "InsightEngine class not exported. " "Check __all__ list in __init__.py"
        )

    def test_remediation_advisor_class(self):
        """Ensure RemediationAdvisor class is exported"""
        assert hasattr(ai_agent, "RemediationAdvisor"), (
            "RemediationAdvisor class not exported. "
            "Check __all__ list in __init__.py"
        )

    def test_incident_reporter_class(self):
        """Ensure IncidentReporter class is exported"""
        assert hasattr(ai_agent, "IncidentReporter"), (
            "IncidentReporter class not exported. " "Check __all__ list in __init__.py"
        )

    def test_postmortem_generator_class(self):
        """Ensure PostmortemGenerator class is exported"""
        assert hasattr(ai_agent, "PostmortemGenerator"), (
            "PostmortemGenerator class not exported. "
            "Check __all__ list in __init__.py"
        )


class TestDynamicImportCompatibility:
    """Test that modules can be accessed via string-based imports"""

    def test_getattr_webhook_server(self):
        """Test getattr-style access to webhook_server"""
        module = getattr(ai_agent, "webhook_server", None)
        assert module is not None, (
            "Cannot access webhook_server via getattr(). "
            "This breaks dynamic imports and some mocking patterns."
        )

    def test_getattr_main(self):
        """Test getattr-style access to main"""
        module = getattr(ai_agent, "main", None)
        assert module is not None, (
            "Cannot access main via getattr(). "
            "This breaks dynamic imports and some mocking patterns."
        )

    def test_module_in_dir_listing(self):
        """Test that modules appear in dir() listing"""
        dir_listing = dir(ai_agent)

        expected_modules = [
            "webhook_server",
            "cli",
            "main",
            "data_collector",
            "incident_analyzer",
            "incident_reporter",
            "insight_engine",
            "postmortem_generator",
            "remediation_advisor",
        ]

        for module_name in expected_modules:
            assert module_name in dir_listing, (
                f"Module '{module_name}' not in dir(ai_agent). "
                "This may cause IDE autocomplete and introspection issues."
            )


class TestMockingCompatibility:
    """Test that the namespace structure supports unittest.mock.patch"""

    def test_can_import_for_patching(self):
        """Test that module path can be constructed for patching"""
        # This test verifies the exact import path that will be used in mocks
        from observability.ai_agent import webhook_server

        assert webhook_server is not None
        assert hasattr(webhook_server, "app")

        # Verify the module can be accessed via full path
        import sys

        assert "observability.ai_agent.webhook_server" in sys.modules

    def test_patch_path_resolves(self):
        """Test that patch paths resolve correctly"""
        # This simulates what unittest.mock.patch does internally
        import importlib

        # Try to resolve the module path
        module = importlib.import_module("observability.ai_agent.webhook_server")
        assert module is not None
        assert hasattr(module, "app")


class TestAllExport:
    """Test that __all__ is properly defined and complete"""

    def test_all_exists(self):
        """Ensure __all__ is defined"""
        assert hasattr(ai_agent, "__all__"), (
            "__all__ not defined in ai_agent/__init__.py. "
            "This is needed for from ai_agent import * and IDE support."
        )

    def test_all_is_list(self):
        """Ensure __all__ is a list"""
        assert isinstance(
            ai_agent.__all__, list
        ), "__all__ should be a list of exported names"

    def test_all_contains_modules(self):
        """Ensure __all__ includes all critical modules"""
        expected_modules = [
            "webhook_server",
            "cli",
            "main",
            "data_collector",
            "incident_analyzer",
            "incident_reporter",
            "insight_engine",
            "postmortem_generator",
            "remediation_advisor",
        ]

        for module_name in expected_modules:
            assert module_name in ai_agent.__all__, (
                f"Module '{module_name}' not in __all__. "
                "This may cause 'from ai_agent import *' to fail."
            )

    def test_all_contains_classes(self):
        """Ensure __all__ includes all critical classes"""
        expected_classes = [
            "IncidentContextCollector",
            "IncidentAnalyzer",
            "InsightEngine",
            "RemediationAdvisor",
            "IncidentReporter",
            "PostmortemGenerator",
        ]

        for class_name in expected_classes:
            assert class_name in ai_agent.__all__, (
                f"Class '{class_name}' not in __all__. "
                "This may cause import issues for users of the library."
            )

    def test_all_exports_are_accessible(self):
        """Ensure all items in __all__ are actually accessible"""
        for name in ai_agent.__all__:
            assert hasattr(ai_agent, name), (
                f"'{name}' is in __all__ but not accessible via ai_agent.{name}. "
                "This indicates a mismatch between __all__ and actual exports."
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
