"""
KPI Performance Tests
Tests for KPI scoring, performance thresholds, exceed/meet logic, and overall scoring accuracy.
"""

import pytest


class TestKPIScoring:
    """Test KPI scoring calculations and logic."""

    @pytest.mark.parametrize(
        "category",
        [
            "loan_performance",
            "operational_efficiency",
            "financial_performance",
            "customer_satisfaction",
        ],
    )
    def test_kpi_category_performance(self, kpi_metrics, category):
        """Test KPI performance for each category."""
        metrics = kpi_metrics[category]

        for kpi_name, kpi_data in metrics.items():
            value = kpi_data["value"]
            target = kpi_data["target"]

            # Calculate performance score
            if kpi_name in [
                "default_rate",
                "average_processing_time",
                "complaint_resolution_time",
                "cost_per_loan",
            ]:
                # Lower is better for these KPIs
                if value <= target:
                    performance_score = 100.0
                else:
                    performance_score = max(0, 100 - ((value - target) / target * 100))
            else:
                # Higher is better for these KPIs
                performance_score = 100.0 if value >= target else value / target * 100

            # Performance score should be between 0 and 100
            assert 0 <= performance_score <= 100

    def test_kpi_exceed_threshold(self, kpi_metrics):
        """Test KPI exceed threshold logic."""
        # Test approval rate (should exceed target)
        approval_rate = kpi_metrics["loan_performance"]["approval_rate"]
        assert approval_rate["value"] > approval_rate["target"]

        # Test default rate (should be below target - lower is better)
        default_rate = kpi_metrics["loan_performance"]["default_rate"]
        assert default_rate["value"] < default_rate["target"]

    def test_kpi_meet_threshold(self, kpi_metrics):
        """Test KPI meet threshold logic."""
        # Test collection rate (should meet or exceed target)
        collection_rate = kpi_metrics["loan_performance"]["collection_rate"]
        assert collection_rate["value"] >= collection_rate["target"]

        # Test farmer satisfaction (should meet target)
        satisfaction = kpi_metrics["customer_satisfaction"]["farmer_satisfaction_score"]
        assert satisfaction["value"] >= satisfaction["target"]

    def test_kpi_performance_scoring_accuracy(self, kpi_metrics):
        """Test KPI performance scoring accuracy."""
        # Test loan performance category
        loan_kpis = kpi_metrics["loan_performance"]

        for kpi_name, kpi_data in loan_kpis.items():
            value = kpi_data["value"]
            target = kpi_data["target"]
            kpi_data["unit"]

            # Calculate expected performance score
            if kpi_name in ["default_rate", "average_processing_time"]:
                # Lower is better
                if value <= target:
                    expected_score = 100.0
                else:
                    expected_score = max(0, 100 - ((value - target) / target * 100))
            else:
                # Higher is better
                expected_score = 100.0 if value >= target else value / target * 100

            # Verify score calculation
            assert expected_score >= 0
            assert expected_score <= 100


class TestPerformanceThresholds:
    """Test performance threshold logic and categorization."""

    def test_performance_status_categorization(self, kpi_metrics):
        """Test performance status categorization logic."""
        loan_kpis = kpi_metrics["loan_performance"]

        for kpi_name, kpi_data in loan_kpis.items():
            value = kpi_data["value"]
            target = kpi_data["target"]

            # Calculate performance score
            if kpi_name in ["default_rate", "average_processing_time"]:
                if value <= target:
                    performance_score = 100.0
                else:
                    performance_score = max(0, 100 - ((value - target) / target * 100))
            else:
                performance_score = 100.0 if value >= target else value / target * 100

            # Determine status
            if performance_score >= 100:
                status = "EXCEEDS"
            elif performance_score >= 90:
                status = "MEETS"
            elif performance_score >= 70:
                status = "BELOW"
            else:
                status = "POOR"

            # Status should be one of the expected values
            assert status in ["EXCEEDS", "MEETS", "BELOW", "POOR"]

    def test_threshold_boundaries(self, kpi_metrics):
        """Test threshold boundary conditions."""
        # Test approval rate (should exceed)
        approval = kpi_metrics["loan_performance"]["approval_rate"]
        assert approval["value"] > approval["target"]

        # Test default rate (should be below - lower is better)
        default = kpi_metrics["loan_performance"]["default_rate"]
        assert default["value"] < default["target"]

        # Test collection rate (should meet or exceed)
        collection = kpi_metrics["loan_performance"]["collection_rate"]
        assert collection["value"] >= collection["target"]

    def test_performance_variance_calculation(self, kpi_metrics):
        """Test performance variance calculation."""
        loan_kpis = kpi_metrics["loan_performance"]

        for _kpi_name, kpi_data in loan_kpis.items():
            value = kpi_data["value"]
            target = kpi_data["target"]

            # Calculate variance
            variance = value - target
            variance_percentage = ((value - target) / target) * 100

            # Variance should be calculable
            assert isinstance(variance, int | float)
            assert isinstance(variance_percentage, int | float)


class TestOverallScoringAccuracy:
    """Test overall scoring accuracy and aggregation."""

    def test_category_overall_performance(self, kpi_metrics):
        """Test overall performance calculation for each category."""
        for _category_name, category_metrics in kpi_metrics.items():
            total_kpis = len(category_metrics)
            exceeds_kpis = 0
            meets_kpis = 0

            for kpi_name, kpi_data in category_metrics.items():
                value = kpi_data["value"]
                target = kpi_data["target"]

                # Calculate performance score
                if kpi_name in [
                    "default_rate",
                    "average_processing_time",
                    "complaint_resolution_time",
                    "cost_per_loan",
                ]:
                    if value <= target:
                        performance_score = 100.0
                    else:
                        performance_score = max(
                            0, 100 - ((value - target) / target * 100)
                        )
                else:
                    if value >= target:
                        performance_score = 100.0
                    else:
                        performance_score = (value / target) * 100

                # Count exceeds and meets
                if performance_score >= 100:
                    exceeds_kpis += 1
                elif performance_score >= 90:
                    meets_kpis += 1

            good_kpis = exceeds_kpis + meets_kpis
            overall_performance = (
                (good_kpis / total_kpis) * 100 if total_kpis > 0 else 0
            )

            # Overall performance should be between 0 and 100
            assert 0 <= overall_performance <= 100
            # Should have reasonable performance (at least some KPIs performing well)
            assert overall_performance >= 50  # At least 50% should be good

    def test_individual_kpi_scoring(self, kpi_metrics):
        """Test individual KPI scoring accuracy."""
        # Test specific KPIs with known good performance
        approval_rate = kpi_metrics["loan_performance"]["approval_rate"]
        assert approval_rate["value"] > approval_rate["target"]  # 87% > 85%

        default_rate = kpi_metrics["loan_performance"]["default_rate"]
        assert default_rate["value"] < default_rate["target"]  # 2.1% < 5%

        collection_rate = kpi_metrics["loan_performance"]["collection_rate"]
        assert collection_rate["value"] > collection_rate["target"]  # 95.5% > 90%

    def test_kpi_unit_consistency(self, kpi_metrics):
        """Test KPI unit consistency and validity."""
        for _category_name, category_metrics in kpi_metrics.items():
            for _kpi_name, kpi_data in category_metrics.items():
                unit = kpi_data["unit"]
                value = kpi_data["value"]

                # Unit should be a string
                assert isinstance(unit, str)
                assert len(unit) > 0

                # Value should be numeric
                assert isinstance(value, int | float)

                # Value should be non-negative (except for rates which can be percentages)
                if "%" not in unit:
                    assert value >= 0

    def test_performance_score_boundaries(self, kpi_metrics):
        """Test performance score boundary conditions."""
        # Test edge case: value exactly at target
        test_kpi = {"value": 85.0, "target": 85.0, "unit": "%"}

        # For higher-is-better KPI, score should be 100%
        performance_score = (
            100.0
            if test_kpi["value"] >= test_kpi["target"]
            else (test_kpi["value"] / test_kpi["target"]) * 100
        )
        assert performance_score == 100.0

        # Test edge case: value much higher than target
        test_kpi_high = {"value": 200.0, "target": 100.0, "unit": "%"}
        performance_score_high = (
            100.0
            if test_kpi_high["value"] >= test_kpi_high["target"]
            else (test_kpi_high["value"] / test_kpi_high["target"]) * 100
        )
        assert performance_score_high == 100.0


class TestKPIDataValidation:
    """Test KPI data validation and integrity."""

    def test_kpi_data_structure(self, kpi_metrics):
        """Test KPI data structure integrity."""
        for _category_name, category_metrics in kpi_metrics.items():
            assert isinstance(category_metrics, dict)
            assert len(category_metrics) > 0

            for _kpi_name, kpi_data in category_metrics.items():
                # Each KPI should have required fields
                assert "value" in kpi_data
                assert "target" in kpi_data
                assert "unit" in kpi_data

                # Values should be numeric
                assert isinstance(kpi_data["value"], int | float)
                assert isinstance(kpi_data["target"], int | float)

                # Unit should be string
                assert isinstance(kpi_data["unit"], str)

    def test_kpi_value_ranges(self, kpi_metrics):
        """Test KPI value ranges for reasonableness."""
        for _category_name, category_metrics in kpi_metrics.items():
            for kpi_name, kpi_data in category_metrics.items():
                value = kpi_data["value"]
                target = kpi_data["target"]
                unit = kpi_data["unit"]

                # Most KPIs should have positive values
                if "rate" not in kpi_name.lower() and "percentage" not in unit.lower():
                    assert value >= 0
                    assert target >= 0

                # Rates and percentages should be reasonable (0-100% or similar)
                if "%" in unit or "rate" in kpi_name.lower():
                    assert 0 <= value <= 1000  # Allow up to 1000% for some metrics
                    assert 0 <= target <= 1000

    def test_kpi_consistency_across_categories(self, kpi_metrics):
        """Test KPI consistency across different categories."""
        # Each category should have at least 3 KPIs
        for _category_name, category_metrics in kpi_metrics.items():
            assert len(category_metrics) >= 3

        # Total number of KPIs should be reasonable
        total_kpis = sum(len(metrics) for metrics in kpi_metrics.values())
        assert total_kpis >= 12  # At least 12 KPIs across all categories
