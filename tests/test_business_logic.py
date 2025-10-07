import pytest

# ---------------------------------------------------------------------
# 🔧 Fixtures & Helpers
# ---------------------------------------------------------------------


@pytest.fixture
def input_data():
    """Sample input data simulating business logic pipeline."""
    return {"farmer_id": 101, "loan_amount": 50000, "term_months": 12, "rate": 8.5}


def calculate_interest(loan_amount: float, rate: float, term_months: int) -> float:
    """Simple interest calculation logic used for validation."""
    return loan_amount * (rate / 100) * (term_months / 12)


def validate_loan_eligibility(data: dict) -> bool:
    """Basic eligibility rule."""
    return data["loan_amount"] >= 10000 and data["term_months"] in [6, 12, 24]


def categorize_risk(loan_amount: float) -> str:
    """Classify risk tier based on loan size."""
    if loan_amount < 20000:
        return "low"
    elif loan_amount < 100000:
        return "medium"
    return "high"


# ---------------------------------------------------------------------
# 🧪 Tests
# ---------------------------------------------------------------------


def test_interest_calculation(input_data):
    """Verify interest calculation returns correct value."""
    result = calculate_interest(
        input_data["loan_amount"], input_data["rate"], input_data["term_months"]
    )
    expected = 50000 * (8.5 / 100) * (12 / 12)
    assert round(result, 2) == round(expected, 2), "Interest calculation mismatch"


def test_loan_eligibility(input_data):
    """Check that loans above 10k and with valid terms are eligible."""
    assert validate_loan_eligibility(input_data), "Loan should be eligible"
    input_data["loan_amount"] = 5000
    assert not validate_loan_eligibility(
        input_data
    ), "Loan should be ineligible for small amounts"


@pytest.mark.parametrize(
    "amount,expected",
    [
        (5000, "low"),
        (50000, "medium"),
        (200000, "high"),
    ],
)
def test_risk_categorization(amount, expected):
    """Risk tier classification should follow correct thresholds."""
    assert (
        categorize_risk(amount) == expected
    ), f"Risk classification mismatch for {amount}"


def test_combined_business_logic(input_data):
    """Integration-style check combining calculations and risk."""
    interest = calculate_interest(
        input_data["loan_amount"], input_data["rate"], input_data["term_months"]
    )
    risk = categorize_risk(input_data["loan_amount"])

    assert interest > 0, "Interest should be positive"
    assert risk in ["low", "medium", "high"], "Risk should be one of the defined tiers"
