"""
Financial Metrics Tests
Tests for payment accuracy, interest calculations, farmer ratios, and collection rates.
"""

import pytest


class TestFinancialCalculations:
    """Test financial calculation accuracy and formulas."""

    def test_collection_rate_accuracy(self, test_data):
        """Test collection rate calculation accuracy."""
        result = test_data["total_collected_amount"] / test_data["total_scheduled_amount"] * 100
        assert round(result, 1) == 33.3

    def test_average_loan_size_calculation(self, test_data):
        """Test average loan size calculation."""
        result = test_data["total_principal"] / test_data["total_loans"]
        assert result == test_data["average_loan_size"]

    def test_outstanding_amount_calculation(self, test_data):
        """Test outstanding amount calculation."""
        result = test_data["total_principal"] - test_data["total_paid"]
        assert result == test_data["total_outstanding"]

    def test_payment_completion_rate(self, test_data):
        """Test payment completion rate calculation."""
        result = (test_data["completed_payments"] / test_data["scheduled_payments"]) * 100
        assert round(result, 1) == test_data["payment_completion_rate"]

    def test_interest_collection_rate(self, test_data):
        """Test interest collection rate calculation."""
        result = (test_data["total_interest_collected"] / test_data["total_interest_charged"]) * 100
        assert round(result, 1) == test_data["interest_collection_rate"]

    def test_farmer_utilization_rate(self, test_data):
        """Test farmer utilization rate calculation."""
        result = (test_data["farmers_with_loans"] / test_data["total_farmers"]) * 100
        assert result == test_data["farmer_utilization_rate"]

    def test_average_farm_size_calculation(self, test_data):
        """Test average farm size calculation."""
        result = test_data["total_farm_area"] / test_data["total_farmers"]
        assert result == test_data["average_farm_size"]

    def test_average_payment_amount(self, test_data):
        """Test average payment amount calculation."""
        result = test_data["total_scheduled_amount"] / test_data["scheduled_payments"]
        assert result == test_data["average_payment_amount"]


class TestPaymentAccuracy:
    """Test payment accuracy and validation."""

    @pytest.mark.parametrize("field,expected", [
        ("completed_payments", 20),
        ("scheduled_payments", 60),
        ("total_collected_amount", 75000.0),
        ("total_scheduled_amount", 225000.0),
    ])
    def test_payment_values_exist(self, test_data, field, expected):
        """Test that payment values exist and are correct."""
        assert test_data[field] == expected

    def test_payment_precision_accuracy(self, test_data):
        """Test payment amount precision."""
        # Test that payment amounts maintain proper precision
        collected = test_data["total_collected_amount"]
        scheduled = test_data["total_scheduled_amount"]
        
        # Both should be properly formatted floats
        assert isinstance(collected, float)
        assert isinstance(scheduled, float)
        
        # Test precision (2 decimal places)
        assert len(str(collected).split('.')[-1]) <= 2
        assert len(str(scheduled).split('.')[-1]) <= 2

    def test_collection_efficiency_calculation(self, test_data):
        """Test collection efficiency calculation."""
        result = (test_data["total_collected_amount"] / test_data["total_scheduled_amount"]) * 100
        assert round(result, 1) == test_data["collection_efficiency"]


class TestInterestCalculations:
    """Test interest calculation accuracy."""

    def test_interest_rate_calculation(self, test_data):
        """Test interest rate calculation."""
        result = (test_data["total_interest_charged"] / test_data["total_principal"]) * 100
        assert round(result, 1) == test_data["average_interest_rate"]

    def test_interest_to_principal_ratio(self, test_data):
        """Test interest to principal ratio calculation."""
        result = (test_data["total_interest_charged"] / test_data["total_principal"]) * 100
        assert round(result, 1) == 10.0

    def test_interest_collection_accuracy(self, test_data):
        """Test interest collection accuracy."""
        # Interest collected should not exceed interest charged
        assert test_data["total_interest_collected"] <= test_data["total_interest_charged"]
        
        # Collection rate should be reasonable (0-100%)
        collection_rate = (test_data["total_interest_collected"] / test_data["total_interest_charged"]) * 100
        assert 0 <= collection_rate <= 100


class TestFarmerMetrics:
    """Test farmer-related metrics and ratios."""

    def test_farmer_counts_consistency(self, test_data):
        """Test farmer count consistency."""
        # Active farmers should not exceed total farmers
        assert test_data["active_farmers"] <= test_data["total_farmers"]
        
        # Farmers with loans should not exceed total farmers
        assert test_data["farmers_with_loans"] <= test_data["total_farmers"]

    def test_farm_area_calculation(self, test_data):
        """Test farm area calculation accuracy."""
        # Total farm area should be sum of individual farm sizes
        # For testing, we'll verify the average calculation
        expected_total = test_data["average_farm_size"] * test_data["total_farmers"]
        assert abs(expected_total - test_data["total_farm_area"]) < 0.1

    def test_farmer_utilization_consistency(self, test_data):
        """Test farmer utilization consistency."""
        utilization = test_data["farmer_utilization_rate"]
        
        # Utilization rate should be between 0 and 100
        assert 0 <= utilization <= 100
        
        # If all farmers have loans, utilization should be 100%
        if test_data["farmers_with_loans"] == test_data["total_farmers"]:
            assert utilization == 100.0


class TestFinancialReportAccuracy:
    """Test financial report calculation accuracy."""

    @pytest.mark.parametrize("scenario_key", [
        "loan_portfolio_summary",
        "monthly_payment_report", 
        "farmer_performance_report",
        "interest_income_report",
    ])
    def test_scenario_calculations(self, test_data, scenario_context, scenario_key):
        """Test calculations for each financial report scenario."""
        scenario = scenario_context[scenario_key]
        calculations = scenario["calculations"]
        
        for metric, formula in calculations.items():
            if formula == "total_principal / total_loans":
                result = test_data["total_principal"] / test_data["total_loans"]
                expected = test_data.get("average_loan_size", 0)
                assert abs(result - expected) < 0.1
                
            elif formula == "(total_paid / total_principal) * 100":
                result = (test_data["total_paid"] / test_data["total_principal"]) * 100
                expected = test_data.get("collection_rate", 0)
                assert abs(result - expected) < 0.1
                
            elif formula == "(total_outstanding / total_principal) * 100":
                result = (test_data["total_outstanding"] / test_data["total_principal"]) * 100
                # Outstanding should be remaining after paid
                expected = ((test_data["total_principal"] - test_data["total_paid"]) / test_data["total_principal"]) * 100
                assert abs(result - expected) < 0.1

    def test_financial_metrics_precision(self, test_data):
        """Test that financial metrics maintain proper precision."""
        precision_fields = [
            "total_principal", "total_paid", "total_outstanding",
            "total_collected_amount", "total_scheduled_amount",
            "total_interest_charged", "total_interest_collected"
        ]
        
        for field in precision_fields:
            value = test_data[field]
            # Should be float
            assert isinstance(value, float)
            # Should have reasonable precision (2 decimal places max)
            decimal_places = len(str(value).split('.')[-1]) if '.' in str(value) else 0
            assert decimal_places <= 2

    def test_financial_ratios_consistency(self, test_data):
        """Test financial ratios for consistency."""
        # Collection rate and collection efficiency should be the same
        collection_rate = (test_data["total_paid"] / test_data["total_principal"]) * 100
        collection_efficiency = (test_data["total_collected_amount"] / test_data["total_scheduled_amount"]) * 100
        
        # These should be close if the data is consistent
        assert abs(collection_rate - collection_efficiency) < 5.0  # 5% tolerance

    def test_interest_metrics_consistency(self, test_data):
        """Test interest metrics for consistency."""
        # Interest collected should not exceed interest charged
        assert test_data["total_interest_collected"] <= test_data["total_interest_charged"]
        
        # Interest rate calculation should be consistent
        calculated_rate = (test_data["total_interest_charged"] / test_data["total_principal"]) * 100
        assert abs(calculated_rate - test_data["average_interest_rate"]) < 0.1
