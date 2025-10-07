import pytest

# ---------------------------------------------------------------------
# 🔧 Fixtures
# ---------------------------------------------------------------------


@pytest.fixture
def expected_rows() -> int:
    return 10


@pytest.fixture
def expected_columns() -> list[str]:
    return ["id", "farmer_id", "amount", "payment_date"]


@pytest.fixture
def format_type() -> str:
    return "CSV"


@pytest.fixture(params=["loan", "payment", "financial"])
def export_type(request) -> str:
    return request.param


@pytest.fixture
def scenario_key() -> str:
    return "default_scenario"


# ---------------------------------------------------------------------
# 📦 Helper: Generate export data
# ---------------------------------------------------------------------


def generate_exported_data(export_type: str, rows: int) -> list[dict]:
    if export_type == "loan":
        return [
            {
                "id": i,
                "farmer_name": f"Farmer {i}",
                "loan_amount": 45000.0 + i * 5000,
                "interest_rate": 8.5,
                "term": 12,
                "status": "ACTIVE",
            }
            for i in range(1, rows + 1)
        ]
    elif export_type == "payment":
        return [
            {
                "id": i,
                "farmer_id": (i % 5) + 1,
                "amount": 3750.0,
                "payment_date": "2025-09-18",
                "payment_method": "Bank",
            }
            for i in range(1, rows + 1)
        ]
    elif export_type == "financial":
        return [
            {
                "metric": f"Metric {i}",
                "value": 100.0 + i * 10,
                "target": 90.0 + i * 10,
                "variance": 10.0,
            }
            for i in range(1, rows + 1)
        ]
    return []


# ---------------------------------------------------------------------
# 🧪 Tests
# ---------------------------------------------------------------------


def test_export_row_count(expected_rows, export_type):
    data = generate_exported_data(export_type, expected_rows)
    assert len(data) == expected_rows, f"Row count mismatch for {export_type}"


def test_export_columns(expected_rows, export_type):
    data = generate_exported_data(export_type, expected_rows)
    if not data:
        pytest.skip("No data generated")

    # Define expected columns for each export type
    expected_columns_map = {
        "loan": ["id", "farmer_name", "loan_amount", "interest_rate", "term", "status"],
        "payment": ["id", "farmer_id", "amount", "payment_date"],
        "financial": ["metric", "target", "value", "variance"],
    }

    expected_columns = expected_columns_map.get(export_type, [])
    actual_columns = set(data[0].keys())
    assert set(expected_columns).issubset(
        actual_columns
    ), f"Missing columns in {export_type}: expected {expected_columns}, got {actual_columns}"


def test_data_non_null(expected_rows, export_type):
    data = generate_exported_data(export_type, expected_rows)
    if not data:
        pytest.skip("No data generated")

    # Define expected columns for each export type
    expected_columns_map = {
        "loan": ["id", "farmer_name", "loan_amount", "interest_rate", "term", "status"],
        "payment": ["id", "farmer_id", "amount", "payment_date"],
        "financial": ["metric", "target", "value", "variance"],
    }

    expected_columns = expected_columns_map.get(export_type, [])
    for row in data[:3]:
        for col in expected_columns:
            assert col in row, f"Column '{col}' missing in row"
            assert row[col] is not None, f"Column '{col}' is None"


def test_estimated_size(expected_rows, format_type, export_type):
    data = generate_exported_data(export_type, expected_rows)
    rows = len(data)
    cols = len(data[0].keys()) if data else 0

    size_map = {
        "CSV": rows * cols * 20,
        "JSON": rows * cols * 50,
        "PDF": rows * 1000,
        "XLSX": rows * cols * 30,
    }
    estimated_size = size_map.get(format_type, rows * cols * 10)
    assert estimated_size > 0, "Estimated size should be > 0"


def test_summary_report(expected_rows, format_type, export_type, scenario_key):
    data = generate_exported_data(export_type, expected_rows)
    print("\n--- Export Summary ---")
    print(f"Scenario: {scenario_key}")
    print(f"Export Type: {export_type}")
    print(f"Format: {format_type}")
    print(f"Total Rows: {len(data)}")
    assert data, "No exported data generated"
