"""
Comprehensive Business Logic Testing for MAGSASA-CARD ERP
Tests agricultural lending logic, workflow validation, and data validation
Refactored from monolithic script to modular pytest suite
"""

import re
from typing import Any

import pytest

# =============================================================================
# 🔧 FIXTURES - Test Data Providers
# =============================================================================


@pytest.fixture
def farmer_profiles():
    """Sample farmer profiles with various AgScore characteristics."""
    return {
        "excellent_farmer": {
            "name": "Carlos Lopez",
            "farm_size": 5.0,
            "years_experience": 15,
            "previous_loans": 3,
            "payment_history": 100.0,
            "crop_diversification": 3,
            "location_risk": "Low",
            "expected_agscore": 850,
            "score_range": (800, 900),
        },
        "good_farmer": {
            "name": "Maria Santos",
            "farm_size": 3.0,
            "years_experience": 8,
            "previous_loans": 2,
            "payment_history": 95.0,
            "crop_diversification": 2,
            "location_risk": "Medium",
            "expected_agscore": 750,
            "score_range": (700, 800),
        },
        "average_farmer": {
            "name": "Juan Dela Cruz",
            "farm_size": 2.0,
            "years_experience": 5,
            "previous_loans": 1,
            "payment_history": 85.0,
            "crop_diversification": 1,
            "location_risk": "Medium",
            "expected_agscore": 650,
            "score_range": (600, 700),
        },
        "new_farmer": {
            "name": "Ana Rodriguez",
            "farm_size": 1.5,
            "years_experience": 2,
            "previous_loans": 0,
            "payment_history": 0.0,
            "crop_diversification": 1,
            "location_risk": "High",
            "expected_agscore": 390,
            "score_range": (350, 450),  # New farmer with no history gets lower score
        },
    }


@pytest.fixture
def interest_rate_scenarios():
    """Interest rate calculation scenarios."""
    return {
        "premium_rice_loan": {
            "loan_type": "Rice Production Loan",
            "agscore": 850,
            "principal": 50000.0,
            "term_months": 12,
            "base_rate": 8.0,
            "final_rate": 6.5,
        },
        "standard_corn_loan": {
            "loan_type": "Corn Production Loan",
            "agscore": 750,
            "principal": 35000.0,
            "term_months": 10,
            "base_rate": 9.0,
            "final_rate": 8.5,
        },
        "equipment_loan": {
            "loan_type": "Equipment Loan",
            "agscore": 650,
            "principal": 75000.0,
            "term_months": 24,
            "base_rate": 12.0,
            "final_rate": 12.0,
        },
        "new_farmer_loan": {
            "loan_type": "New Farmer Loan",
            "agscore": 550,
            "principal": 25000.0,
            "term_months": 8,
            "base_rate": 10.0,
            "final_rate": 11.0,
        },
    }


@pytest.fixture
def payment_schedule_scenarios():
    """Payment schedule calculation scenarios."""
    return {
        "standard_loan": {
            "principal": 45000.0,
            "annual_rate": 8.5,
            "term_months": 12,
            "expected_monthly_payment": 3937.50,
        },
        "short_term_loan": {
            "principal": 25000.0,
            "annual_rate": 10.0,
            "term_months": 6,
            "expected_monthly_payment": 4280.00,
        },
        "equipment_loan": {
            "principal": 75000.0,
            "annual_rate": 12.0,
            "term_months": 24,
            "expected_monthly_payment": 3533.00,
        },
    }


@pytest.fixture
def late_fee_scenarios():
    """Late fee calculation scenarios."""
    return {
        "minor_delay": {
            "payment_amount": 3750.0,
            "days_late": 5,
            "late_fee_rate": 0.05,
            "grace_period": 3,
            "expected_fee": 12.50,  # (5-3) * (3750 * 0.05 / 30) = 2 * 6.25 = 12.50
        },
        "moderate_delay": {
            "payment_amount": 4200.0,
            "days_late": 15,
            "late_fee_rate": 0.05,
            "grace_period": 3,
            "expected_fee": 84.00,  # (15-3) * (4200 * 0.05 / 30) = 12 * 7.00 = 84.00
        },
        "severe_delay": {
            "payment_amount": 5000.0,
            "days_late": 45,
            "late_fee_rate": 0.05,
            "grace_period": 3,
            "expected_fee": 350.00,
        },
        "grace_period": {
            "payment_amount": 3000.0,
            "days_late": 2,
            "late_fee_rate": 0.05,
            "grace_period": 3,
            "expected_fee": 0.0,
        },
    }


@pytest.fixture
def loan_limit_scenarios():
    """Loan limit enforcement scenarios."""
    return {
        "within_limit": {
            "farmer_agscore": 800,
            "existing_loans": 25000.0,
            "new_loan_request": 30000.0,
            "annual_income": 25000.0,
            "should_approve": True,
        },
        "exceeds_total_limit": {
            "farmer_agscore": 750,
            "existing_loans": 40000.0,
            "new_loan_request": 50000.0,
            "annual_income": 20000.0,
            "should_approve": False,
        },
        "low_agscore_limit": {
            "farmer_agscore": 550,
            "existing_loans": 0.0,
            "new_loan_request": 40000.0,
            "annual_income": 15000.0,
            "should_approve": False,
        },
        "premium_farmer": {
            "farmer_agscore": 850,
            "existing_loans": 10000.0,
            "new_loan_request": 60000.0,
            "annual_income": 30000.0,
            "should_approve": True,
        },
    }


@pytest.fixture
def approval_workflow_scenarios():
    """Loan approval workflow scenarios."""
    return {
        "small_loan_auto_approval": {
            "loan_amount": 15000.0,
            "farmer_agscore": 800,
            "loan_type": "Rice Production",
            "auto_approval_limit": 20000.0,
            "expected_workflow": ["SUBMITTED", "AUTO_APPROVED", "DISBURSED"],
            "approval_levels": 1,
        },
        "medium_loan_officer_approval": {
            "loan_amount": 35000.0,
            "farmer_agscore": 750,
            "loan_type": "Corn Production",
            "auto_approval_limit": 20000.0,
            "expected_workflow": [
                "SUBMITTED",
                "OFFICER_REVIEW",
                "OFFICER_APPROVED",
                "DISBURSED",
            ],
            "approval_levels": 2,
        },
        "large_loan_manager_approval": {
            "loan_amount": 75000.0,
            "farmer_agscore": 700,
            "loan_type": "Equipment Purchase",
            "auto_approval_limit": 20000.0,
            "expected_workflow": [
                "SUBMITTED",
                "OFFICER_REVIEW",
                "MANAGER_REVIEW",
                "MANAGER_APPROVED",
                "DISBURSED",
            ],
            "approval_levels": 3,
        },
        "high_risk_rejection": {
            "loan_amount": 50000.0,
            "farmer_agscore": 450,
            "loan_type": "New Farmer Loan",
            "auto_approval_limit": 20000.0,
            "expected_workflow": ["SUBMITTED", "OFFICER_REVIEW", "REJECTED"],
            "approval_levels": 2,
        },
    }


@pytest.fixture
def status_transitions():
    """Valid status transition rules and test scenarios."""
    valid_transitions = {
        "DRAFT": ["SUBMITTED", "CANCELLED"],
        "SUBMITTED": ["UNDER_REVIEW", "CANCELLED"],
        "UNDER_REVIEW": ["APPROVED", "REJECTED", "PENDING_INFO"],
        "PENDING_INFO": ["UNDER_REVIEW", "CANCELLED"],
        "APPROVED": ["DISBURSED", "CANCELLED"],
        "DISBURSED": ["ACTIVE"],
        "ACTIVE": ["COMPLETED", "DEFAULTED"],
        "COMPLETED": [],
        "REJECTED": [],
        "CANCELLED": [],
        "DEFAULTED": ["ACTIVE"],
    }

    test_scenarios = [
        {"from": "DRAFT", "to": "SUBMITTED", "should_allow": True},
        {"from": "SUBMITTED", "to": "UNDER_REVIEW", "should_allow": True},
        {"from": "UNDER_REVIEW", "to": "APPROVED", "should_allow": True},
        {"from": "APPROVED", "to": "DISBURSED", "should_allow": True},
        {"from": "DISBURSED", "to": "ACTIVE", "should_allow": True},
        {"from": "ACTIVE", "to": "COMPLETED", "should_allow": True},
        {"from": "DRAFT", "to": "APPROVED", "should_allow": False},
        {"from": "COMPLETED", "to": "ACTIVE", "should_allow": False},
        {"from": "REJECTED", "to": "APPROVED", "should_allow": False},
        {"from": "UNDER_REVIEW", "to": "PENDING_INFO", "should_allow": True},
        {"from": "PENDING_INFO", "to": "UNDER_REVIEW", "should_allow": True},
        {"from": "DEFAULTED", "to": "ACTIVE", "should_allow": True},
    ]

    return {"valid_transitions": valid_transitions, "test_scenarios": test_scenarios}


@pytest.fixture
def notification_scenarios():
    """Notification routing scenarios."""
    return {
        "loan_approval": {
            "event": "Loan Approved",
            "priority": "HIGH",
            "expected_recipients": ["farmer", "officer"],
            "expected_channels": ["SMS", "Email", "In-App"],
        },
        "payment_due": {
            "event": "Payment Due (3 days)",
            "priority": "MEDIUM",
            "expected_recipients": ["farmer"],
            "expected_channels": ["SMS", "In-App"],
        },
        "payment_overdue": {
            "event": "Payment Overdue",
            "priority": "HIGH",
            "expected_recipients": ["farmer", "officer", "manager"],
            "expected_channels": ["SMS", "Email", "In-App", "Phone"],
        },
        "loan_completion": {
            "event": "Loan Completed",
            "priority": "LOW",
            "expected_recipients": ["farmer", "officer"],
            "expected_channels": ["SMS", "Email", "In-App"],
        },
    }


@pytest.fixture
def validation_scenarios():
    """Input validation test scenarios."""
    return {
        "farmer_registration": {
            "form_type": "Farmer Registration",
            "test_data": {
                "full_name": "Juan Dela Cruz",
                "phone": "09171234567",
                "email": "juan@email.com",
                "farm_size": 2.5,
                "location": "Laguna",
                "crop_type": "Rice",
            },
            "validation_rules": {
                "full_name": {"required": True, "min_length": 2, "max_length": 100},
                "phone": {"required": True, "pattern": r"^09\d{9}$"},
                "email": {"required": False, "pattern": r"^[^@]+@[^@]+\.[^@]+$"},
                "farm_size": {"required": True, "min": 0.1, "max": 100.0},
                "location": {"required": True, "min_length": 2},
                "crop_type": {
                    "required": True,
                    "options": ["Rice", "Corn", "Vegetables"],
                },
            },
            "should_pass": True,
        },
        "loan_application": {
            "form_type": "Loan Application",
            "test_data": {
                "loan_amount": 45000.0,
                "loan_purpose": "Rice Production",
                "term_months": 12,
                "collateral_type": "Land Title",
                "collateral_value": 150000.0,
            },
            "validation_rules": {
                "loan_amount": {"required": True, "min": 5000.0, "max": 500000.0},
                "loan_purpose": {
                    "required": True,
                    "options": ["Rice Production", "Corn Production", "Equipment"],
                },
                "term_months": {"required": True, "min": 3, "max": 36},
                "collateral_type": {
                    "required": True,
                    "options": ["Land Title", "Equipment", "Crop Insurance"],
                },
                "collateral_value": {"required": True, "min": 1000.0},
            },
            "should_pass": True,
        },
        "invalid_phone": {
            "form_type": "Farmer Registration",
            "test_data": {
                "full_name": "Maria Santos",
                "phone": "123456789",
                "farm_size": 1.5,
                "location": "Bataan",
                "crop_type": "Corn",
            },
            "validation_rules": {"phone": {"required": True, "pattern": r"^09\d{9}$"}},
            "should_pass": False,
        },
    }


@pytest.fixture
def business_rule_scenarios():
    """Agricultural business rule scenarios."""
    return {
        "seasonal_crop_timing": {
            "rule": "Rice planting season constraint",
            "crop_type": "Rice",
            "planting_month": 6,
            "valid_months": [5, 6, 7, 11, 12, 1],
            "should_allow": True,
        },
        "loan_to_income_ratio": {
            "rule": "Loan-to-income ratio limit",
            "annual_income": 50000.0,
            "loan_amount": 120000.0,
            "max_ratio": 3.0,
            "should_allow": False,
        },
        "collateral_coverage": {
            "rule": "Collateral coverage requirement",
            "loan_amount": 75000.0,
            "collateral_value": 100000.0,
            "min_coverage_ratio": 1.2,
            "should_allow": True,
        },
        "farm_size_loan_limit": {
            "rule": "Farm size-based loan limit",
            "farm_size": 1.0,
            "loan_amount": 80000.0,
            "max_per_hectare": 50000.0,
            "should_allow": False,
        },
    }


# =============================================================================
# 🧮 HELPER FUNCTIONS - Business Logic Implementation
# =============================================================================


def calculate_agscore(farmer_data: dict[str, Any]) -> int:
    """Calculate AgScore based on farmer data."""
    score = 300  # Base score

    # Farm size factor (0-150 points)
    farm_size = farmer_data["farm_size"]
    if farm_size >= 5.0:
        score += 150
    elif farm_size >= 3.0:
        score += 120
    elif farm_size >= 2.0:
        score += 90
    elif farm_size >= 1.0:
        score += 60
    else:
        score += 30

    # Experience factor (0-100 points)
    experience = farmer_data["years_experience"]
    if experience >= 15:
        score += 100
    elif experience >= 10:
        score += 80
    elif experience >= 5:
        score += 60
    elif experience >= 2:
        score += 40
    else:
        score += 20

    # Payment history factor (0-200 points)
    payment_history = farmer_data["payment_history"]
    if payment_history >= 98:
        score += 200
    elif payment_history >= 95:
        score += 180
    elif payment_history >= 90:
        score += 150
    elif payment_history >= 80:
        score += 100
    elif payment_history >= 70:
        score += 50
    else:
        score += 0

    # Loan history factor (0-100 points)
    previous_loans = farmer_data["previous_loans"]
    if previous_loans >= 3:
        score += 100
    elif previous_loans >= 2:
        score += 80
    elif previous_loans >= 1:
        score += 60
    else:
        score += 20

    # Diversification factor (0-50 points)
    diversification = farmer_data["crop_diversification"]
    score += min(diversification * 20, 50)

    # Location risk factor (-50 to 0 points)
    location_risk = farmer_data["location_risk"]
    if location_risk == "Low":
        score += 0
    elif location_risk == "Medium":
        score -= 25
    else:
        score -= 50

    return min(max(score, 300), 900)


def calculate_interest_rate(agscore: int, loan_type: str, base_rate: float) -> float:
    """Calculate interest rate based on AgScore and loan type."""
    if agscore >= 800:
        adjustment = -1.5
    elif agscore >= 700:
        adjustment = -0.5
    elif agscore >= 600:
        adjustment = 0.0
    else:
        adjustment = 1.0

    if "Equipment" in loan_type or "New Farmer" in loan_type:
        adjustment += 0.5

    final_rate = base_rate + adjustment
    return max(final_rate, 5.0)


def calculate_payment_schedule(
    principal: float, annual_rate: float, term_months: int
) -> tuple[float, list[dict]]:
    """Calculate payment schedule."""
    monthly_rate = annual_rate / 12 / 100

    if monthly_rate > 0:
        monthly_payment = (
            principal
            * (monthly_rate * (1 + monthly_rate) ** term_months)
            / ((1 + monthly_rate) ** term_months - 1)
        )
    else:
        monthly_payment = principal / term_months

    schedule = []
    remaining_balance = principal

    for month in range(1, term_months + 1):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment

        schedule.append(
            {
                "month": month,
                "payment": monthly_payment,
                "principal": principal_payment,
                "interest": interest_payment,
                "balance": max(remaining_balance, 0),
            }
        )

    return monthly_payment, schedule


def calculate_late_fee(
    payment_amount: float, days_late: int, late_fee_rate: float, grace_period: int
) -> float:
    """Calculate late fee based on days late."""
    if days_late <= grace_period:
        return 0.0

    daily_rate = late_fee_rate / 30
    chargeable_days = days_late - grace_period
    late_fee = payment_amount * daily_rate * chargeable_days
    return round(late_fee, 2)


def check_loan_limit(
    agscore: int, existing_loans: float, new_loan: float, annual_income: float
) -> tuple[bool, float]:
    """Check if loan request is within limits."""
    if agscore >= 800:
        multiplier = 4.0
    elif agscore >= 700:
        multiplier = 3.0
    elif agscore >= 600:
        multiplier = 2.5
    else:
        multiplier = 2.0

    max_total_limit = annual_income * multiplier
    total_exposure = existing_loans + new_loan
    single_loan_limit = max_total_limit * 0.8

    within_total_limit = total_exposure <= max_total_limit
    within_single_limit = new_loan <= single_loan_limit

    return within_total_limit and within_single_limit, max_total_limit


def determine_approval_workflow(
    loan_amount: float, agscore: int, loan_type: str, auto_limit: float
) -> tuple[list[str], int]:
    """Determine approval workflow based on loan characteristics."""
    workflow = ["SUBMITTED"]

    if loan_amount <= auto_limit and agscore >= 700:
        workflow.extend(["AUTO_APPROVED", "DISBURSED"])
        return workflow, 1

    workflow.append("OFFICER_REVIEW")

    if agscore < 500 or (loan_amount > 50000 and agscore < 600):
        workflow.append("REJECTED")
        return workflow, 2

    if loan_amount > 50000 or "Equipment" in loan_type:
        workflow.extend(["MANAGER_REVIEW", "MANAGER_APPROVED", "DISBURSED"])
        return workflow, 3
    else:
        workflow.extend(["OFFICER_APPROVED", "DISBURSED"])
        return workflow, 2


def is_valid_transition(
    from_status: str, to_status: str, valid_transitions: dict[str, list[str]]
) -> bool:
    """Check if status transition is valid."""
    return to_status in valid_transitions.get(from_status, [])


def generate_notifications(event: str, priority: str) -> tuple[list[str], list[str]]:
    """Generate notifications based on event and priority."""
    notifications = []

    if "Approval" in event or "Approved" in event:
        notifications.extend(["farmer", "officer"])
        channels = ["SMS", "Email", "In-App"]
    elif "Due" in event:
        notifications.extend(["farmer"])
        channels = ["SMS", "In-App"]
    elif "Overdue" in event:
        notifications.extend(["farmer", "officer", "manager"])
        channels = ["SMS", "Email", "In-App", "Phone"]
    elif "Completion" in event or "Completed" in event:
        notifications.extend(["farmer", "officer"])
        channels = ["SMS", "Email", "In-App"]
    else:
        notifications.extend(["farmer"])
        channels = ["In-App"]

    return notifications, channels


def validate_input(
    data: dict[str, Any], rules: dict[str, dict]
) -> tuple[bool, list[str]]:
    """Validate input data against rules."""
    errors = []

    for field, rule in rules.items():
        value = data.get(field)

        if rule.get("required", False) and not value:
            errors.append(f"{field} is required")
            continue

        if value is None:
            continue

        if isinstance(value, str):
            if "min_length" in rule and len(value) < rule["min_length"]:
                errors.append(f"{field} too short")
            if "max_length" in rule and len(value) > rule["max_length"]:
                errors.append(f"{field} too long")
            if "pattern" in rule and not re.match(rule["pattern"], value):
                errors.append(f"{field} invalid format")
            if "options" in rule and value not in rule["options"]:
                errors.append(f"{field} invalid option")

        if isinstance(value, int | float):
            if "min" in rule and value < rule["min"]:
                errors.append(f"{field} too small")
            if "max" in rule and value > rule["max"]:
                errors.append(f"{field} too large")

    return len(errors) == 0, errors


def check_business_rule(rule_type: str, **kwargs) -> bool:
    """Check business rule compliance."""
    # Extract kwargs to avoid passing test metadata
    filtered_kwargs = {
        k: v
        for k, v in kwargs.items()
        if k not in ("rule", "should_allow", "crop_type")
    }

    if "season" in rule_type.lower():
        planting_month = filtered_kwargs.get("planting_month")
        valid_months = filtered_kwargs.get("valid_months")
        if planting_month is None or valid_months is None:
            return False
        return planting_month in valid_months

    elif "income_ratio" in rule_type.lower():
        annual_income = filtered_kwargs["annual_income"]
        loan_amount = filtered_kwargs["loan_amount"]
        max_ratio = filtered_kwargs["max_ratio"]
        return loan_amount <= annual_income * max_ratio

    elif "collateral" in rule_type.lower():
        loan_amount = filtered_kwargs["loan_amount"]
        collateral_value = filtered_kwargs["collateral_value"]
        min_coverage = filtered_kwargs["min_coverage_ratio"]
        return collateral_value >= loan_amount * min_coverage

    elif "farm_size" in rule_type.lower():
        farm_size = filtered_kwargs["farm_size"]
        loan_amount = filtered_kwargs["loan_amount"]
        max_per_hectare = filtered_kwargs["max_per_hectare"]
        return loan_amount <= farm_size * max_per_hectare

    return False


# =============================================================================
# 🧪 TEST CLASSES - Organized by Domain
# =============================================================================


class TestLoanApprovalWorkflow:
    """Tests for loan approval workflow, credit scoring, interest, and limits."""

    def test_agscore_calculation_excellent_farmer(self, farmer_profiles):
        """Excellent farmer should receive AgScore in premium range."""
        farmer = farmer_profiles["excellent_farmer"]
        score = calculate_agscore(farmer)

        assert (
            farmer["score_range"][0] <= score <= farmer["score_range"][1]
        ), f"Score {score} not in expected range {farmer['score_range']}"
        assert (
            abs(score - farmer["expected_agscore"]) <= 50
        ), f"Score {score} too far from expected {farmer['expected_agscore']}"

    def test_agscore_calculation_good_farmer(self, farmer_profiles):
        """Good farmer should receive AgScore in good range."""
        farmer = farmer_profiles["good_farmer"]
        score = calculate_agscore(farmer)

        assert farmer["score_range"][0] <= score <= farmer["score_range"][1]
        assert abs(score - farmer["expected_agscore"]) <= 50

    def test_agscore_calculation_average_farmer(self, farmer_profiles):
        """Average farmer should receive AgScore in average range."""
        farmer = farmer_profiles["average_farmer"]
        score = calculate_agscore(farmer)

        assert farmer["score_range"][0] <= score <= farmer["score_range"][1]
        assert abs(score - farmer["expected_agscore"]) <= 50

    def test_agscore_calculation_new_farmer(self, farmer_profiles):
        """New farmer should receive AgScore in lower range."""
        farmer = farmer_profiles["new_farmer"]
        score = calculate_agscore(farmer)

        assert farmer["score_range"][0] <= score <= farmer["score_range"][1]
        assert abs(score - farmer["expected_agscore"]) <= 50

    @pytest.mark.parametrize(
        "scenario_key",
        [
            "premium_rice_loan",
            "standard_corn_loan",
            "equipment_loan",
            "new_farmer_loan",
        ],
    )
    def test_interest_rate_computation(self, interest_rate_scenarios, scenario_key):
        """Interest rates should be calculated accurately based on AgScore and loan type."""
        scenario = interest_rate_scenarios[scenario_key]
        calculated_rate = calculate_interest_rate(
            scenario["agscore"], scenario["loan_type"], scenario["base_rate"]
        )

        assert (
            abs(calculated_rate - scenario["final_rate"]) <= 0.5
        ), f"Rate {calculated_rate}% not close to expected {scenario['final_rate']}%"

    @pytest.mark.parametrize(
        "scenario_key", ["standard_loan", "short_term_loan", "equipment_loan"]
    )
    def test_payment_schedule_accuracy(self, payment_schedule_scenarios, scenario_key):
        """Payment schedules should be calculated accurately."""
        scenario = payment_schedule_scenarios[scenario_key]
        monthly_payment, schedule = calculate_payment_schedule(
            scenario["principal"], scenario["annual_rate"], scenario["term_months"]
        )

        # Check payment accuracy (within 1%)
        expected = scenario["expected_monthly_payment"]
        assert (
            abs(monthly_payment - expected) / expected <= 0.01
        ), f"Payment ₱{monthly_payment:,.2f} not close to expected ₱{expected:,.2f}"

        # Verify schedule integrity
        total_principal = sum(payment["principal"] for payment in schedule)
        assert (
            abs(total_principal - scenario["principal"]) <= 1.0
        ), "Total principal payments don't match loan amount"

        assert (
            schedule[-1]["balance"] <= 1.0
        ), f"Final balance {schedule[-1]['balance']} should be near zero"

    @pytest.mark.parametrize(
        "scenario_key",
        ["within_limit", "exceeds_total_limit", "low_agscore_limit", "premium_farmer"],
    )
    def test_loan_limit_enforcement(self, loan_limit_scenarios, scenario_key):
        """Loan limits should be enforced correctly based on AgScore and income."""
        scenario = loan_limit_scenarios[scenario_key]
        approved, calculated_limit = check_loan_limit(
            scenario["farmer_agscore"],
            scenario["existing_loans"],
            scenario["new_loan_request"],
            scenario["annual_income"],
        )

        assert (
            approved == scenario["should_approve"]
        ), f"Loan approval decision incorrect for {scenario_key}"

    @pytest.mark.parametrize(
        "scenario_key",
        [
            "small_loan_auto_approval",
            "medium_loan_officer_approval",
            "large_loan_manager_approval",
            "high_risk_rejection",
        ],
    )
    def test_approval_workflow_routing(self, approval_workflow_scenarios, scenario_key):
        """Approval workflows should route correctly based on amount and risk."""
        scenario = approval_workflow_scenarios[scenario_key]
        workflow, levels = determine_approval_workflow(
            scenario["loan_amount"],
            scenario["farmer_agscore"],
            scenario["loan_type"],
            scenario["auto_approval_limit"],
        )

        assert (
            workflow == scenario["expected_workflow"]
        ), f"Workflow {workflow} doesn't match expected {scenario['expected_workflow']}"
        assert (
            levels == scenario["approval_levels"]
        ), f"Approval levels {levels} don't match expected {scenario['approval_levels']}"


class TestLateFeeCalculation:
    """Tests for late fee calculation logic."""

    @pytest.mark.parametrize(
        "scenario_key",
        ["minor_delay", "moderate_delay", "severe_delay", "grace_period"],
    )
    def test_late_fee_computation(self, late_fee_scenarios, scenario_key):
        """Late fees should be calculated correctly with grace period."""
        scenario = late_fee_scenarios[scenario_key]
        calculated_fee = calculate_late_fee(
            scenario["payment_amount"],
            scenario["days_late"],
            scenario["late_fee_rate"],
            scenario["grace_period"],
        )

        assert (
            abs(calculated_fee - scenario["expected_fee"]) <= 1.0
        ), f"Fee ₱{calculated_fee:.2f} not close to expected ₱{scenario['expected_fee']:.2f}"

    def test_late_fee_grace_period_no_charge(self, late_fee_scenarios):
        """No late fee should be charged within grace period."""
        scenario = late_fee_scenarios["grace_period"]
        fee = calculate_late_fee(
            scenario["payment_amount"],
            scenario["days_late"],
            scenario["late_fee_rate"],
            scenario["grace_period"],
        )

        assert fee == 0.0, "Fee should be zero within grace period"

    def test_late_fee_increases_with_days(self):
        """Late fee should increase proportionally with days late."""
        payment = 5000.0
        rate = 0.05
        grace = 3

        fee_5_days = calculate_late_fee(payment, 5, rate, grace)
        fee_10_days = calculate_late_fee(payment, 10, rate, grace)
        fee_20_days = calculate_late_fee(payment, 20, rate, grace)

        assert fee_10_days > fee_5_days, "Fee should increase with days"
        assert fee_20_days > fee_10_days, "Fee should increase with days"


class TestStateMachineTransitions:
    """Tests for loan status state machine transitions."""

    def test_valid_forward_transitions(self, status_transitions):
        """Valid forward transitions should be allowed."""
        valid_trans = status_transitions["valid_transitions"]

        assert is_valid_transition("DRAFT", "SUBMITTED", valid_trans)
        assert is_valid_transition("SUBMITTED", "UNDER_REVIEW", valid_trans)
        assert is_valid_transition("UNDER_REVIEW", "APPROVED", valid_trans)
        assert is_valid_transition("APPROVED", "DISBURSED", valid_trans)
        assert is_valid_transition("DISBURSED", "ACTIVE", valid_trans)
        assert is_valid_transition("ACTIVE", "COMPLETED", valid_trans)

    def test_invalid_skip_transitions(self, status_transitions):
        """Invalid skip transitions should be blocked."""
        valid_trans = status_transitions["valid_transitions"]

        assert not is_valid_transition("DRAFT", "APPROVED", valid_trans)
        assert not is_valid_transition("SUBMITTED", "DISBURSED", valid_trans)
        assert not is_valid_transition("UNDER_REVIEW", "ACTIVE", valid_trans)

    def test_terminal_state_transitions(self, status_transitions):
        """Terminal states should not allow transitions."""
        valid_trans = status_transitions["valid_transitions"]

        assert not is_valid_transition("COMPLETED", "ACTIVE", valid_trans)
        assert not is_valid_transition("REJECTED", "APPROVED", valid_trans)
        assert not is_valid_transition("CANCELLED", "SUBMITTED", valid_trans)

    def test_pending_info_cycle(self, status_transitions):
        """Pending info cycle should work correctly."""
        valid_trans = status_transitions["valid_transitions"]

        assert is_valid_transition("UNDER_REVIEW", "PENDING_INFO", valid_trans)
        assert is_valid_transition("PENDING_INFO", "UNDER_REVIEW", valid_trans)

    def test_defaulted_reactivation(self, status_transitions):
        """Defaulted loans should be reactivatable."""
        valid_trans = status_transitions["valid_transitions"]

        assert is_valid_transition("DEFAULTED", "ACTIVE", valid_trans)

    @pytest.mark.parametrize(
        "scenario",
        [
            {"from": "DRAFT", "to": "SUBMITTED", "should_allow": True},
            {"from": "SUBMITTED", "to": "UNDER_REVIEW", "should_allow": True},
            {"from": "UNDER_REVIEW", "to": "APPROVED", "should_allow": True},
            {"from": "DRAFT", "to": "APPROVED", "should_allow": False},
            {"from": "COMPLETED", "to": "ACTIVE", "should_allow": False},
            {"from": "REJECTED", "to": "APPROVED", "should_allow": False},
        ],
    )
    def test_transition_scenarios(self, status_transitions, scenario):
        """All transition scenarios should behave correctly."""
        valid_trans = status_transitions["valid_transitions"]
        result = is_valid_transition(scenario["from"], scenario["to"], valid_trans)

        assert (
            result == scenario["should_allow"]
        ), f"Transition {scenario['from']} → {scenario['to']} incorrectly handled"


class TestNotificationSystem:
    """Tests for automated notification routing."""

    @pytest.mark.parametrize(
        "scenario_key",
        ["loan_approval", "payment_due", "payment_overdue", "loan_completion"],
    )
    def test_notification_routing(self, notification_scenarios, scenario_key):
        """Notifications should route to correct recipients and channels."""
        scenario = notification_scenarios[scenario_key]
        recipients, channels = generate_notifications(
            scenario["event"], scenario["priority"]
        )

        assert set(recipients) == set(
            scenario["expected_recipients"]
        ), f"Recipients {recipients} don't match expected {scenario['expected_recipients']}"
        assert set(channels) == set(
            scenario["expected_channels"]
        ), f"Channels {channels} don't match expected {scenario['expected_channels']}"

    def test_high_priority_overdue_notifications(self, notification_scenarios):
        """Overdue payments should notify all stakeholders through all channels."""
        scenario = notification_scenarios["payment_overdue"]
        recipients, channels = generate_notifications(
            scenario["event"], scenario["priority"]
        )

        assert "farmer" in recipients
        assert "officer" in recipients
        assert "manager" in recipients
        assert "Phone" in channels, "Overdue should include phone notification"

    def test_low_priority_completion_notifications(self, notification_scenarios):
        """Completion events should have simpler notification."""
        scenario = notification_scenarios["loan_completion"]
        recipients, channels = generate_notifications(
            scenario["event"], scenario["priority"]
        )

        assert "farmer" in recipients
        assert "officer" in recipients
        assert "manager" not in recipients, "Manager not needed for completion"


class TestFormValidation:
    """Tests for form input validation."""

    def test_valid_farmer_registration(self, validation_scenarios):
        """Valid farmer registration should pass all validations."""
        scenario = validation_scenarios["farmer_registration"]
        is_valid, errors = validate_input(
            scenario["test_data"], scenario["validation_rules"]
        )

        assert is_valid, f"Valid data should pass: {errors}"
        assert len(errors) == 0

    def test_valid_loan_application(self, validation_scenarios):
        """Valid loan application should pass all validations."""
        scenario = validation_scenarios["loan_application"]
        is_valid, errors = validate_input(
            scenario["test_data"], scenario["validation_rules"]
        )

        assert is_valid, f"Valid data should pass: {errors}"
        assert len(errors) == 0

    def test_invalid_phone_format(self, validation_scenarios):
        """Invalid phone format should be rejected."""
        scenario = validation_scenarios["invalid_phone"]
        is_valid, errors = validate_input(
            scenario["test_data"], scenario["validation_rules"]
        )

        assert not is_valid, "Invalid phone should fail validation"
        assert len(errors) > 0
        assert any("phone" in error.lower() for error in errors)

    def test_required_field_validation(self):
        """Required fields should be enforced."""
        data = {"full_name": ""}
        rules = {"full_name": {"required": True, "min_length": 2}}

        is_valid, errors = validate_input(data, rules)

        assert not is_valid
        assert any("required" in error.lower() for error in errors)

    def test_numeric_range_validation(self):
        """Numeric ranges should be enforced."""
        data = {"loan_amount": 1000.0}
        rules = {"loan_amount": {"required": True, "min": 5000.0, "max": 500000.0}}

        is_valid, errors = validate_input(data, rules)

        assert not is_valid
        assert any("too small" in error.lower() for error in errors)

    def test_pattern_validation(self):
        """Pattern validation should work correctly."""
        data = {"email": "invalid-email"}
        rules = {"email": {"required": True, "pattern": r"^[^@]+@[^@]+\.[^@]+$"}}

        is_valid, errors = validate_input(data, rules)

        assert not is_valid
        assert any("invalid format" in error.lower() for error in errors)


class TestBusinessRuleCompliance:
    """Tests for agricultural business rule enforcement."""

    @pytest.mark.parametrize(
        "scenario_key",
        [
            "seasonal_crop_timing",
            "loan_to_income_ratio",
            "collateral_coverage",
            "farm_size_loan_limit",
        ],
    )
    def test_business_rule_compliance(self, business_rule_scenarios, scenario_key):
        """Business rules should be enforced correctly."""
        scenario = business_rule_scenarios[scenario_key]
        rule_compliant = check_business_rule(scenario["rule"], **scenario)

        assert (
            rule_compliant == scenario["should_allow"]
        ), f"Rule '{scenario['rule']}' incorrectly enforced"

    def test_seasonal_planting_valid_month(self, business_rule_scenarios):
        """Rice planting in valid season should be allowed."""
        scenario = business_rule_scenarios["seasonal_crop_timing"]
        compliant = check_business_rule(scenario["rule"], **scenario)

        assert compliant, "Valid planting month should be allowed"

    def test_loan_to_income_ratio_enforcement(self, business_rule_scenarios):
        """Excessive loan-to-income ratios should be rejected."""
        scenario = business_rule_scenarios["loan_to_income_ratio"]
        compliant = check_business_rule(scenario["rule"], **scenario)

        assert not compliant, "Excessive loan-to-income ratio should be rejected"

    def test_collateral_coverage_requirement(self, business_rule_scenarios):
        """Adequate collateral coverage should be required."""
        scenario = business_rule_scenarios["collateral_coverage"]
        compliant = check_business_rule(scenario["rule"], **scenario)

        assert compliant, "Adequate collateral should pass"

    def test_farm_size_loan_limit(self, business_rule_scenarios):
        """Loan amounts should be limited by farm size."""
        scenario = business_rule_scenarios["farm_size_loan_limit"]
        compliant = check_business_rule(scenario["rule"], **scenario)

        assert not compliant, "Excessive loan for farm size should be rejected"
