from datetime import datetime, timedelta
import pytest

from src.api.server import app


@pytest.fixture
def client():
    # Use the Flask test client to make requests during testing
    with app.test_client() as client:
        yield client


def test_valid_request_w_tracked_token(client):
    # Test a valid request with a tracked token
    res = client.get(
        "/chart-data",
        query_string={"token_symbol": "WBTC", "time_unit_in_hours": "24"},
    )
    assert res.status_code == 200
    # Data should exist
    assert len(res.json) > 0
    # There should be rows with matching labels
    labels = {"open", "close", "high", "low", "priceUSD"}
    for row in res.json:
        assert row[0][1] in labels
        # Ensure 3D array
        assert len(row) > 0


def test_valid_steps_w_tracked_token(client):
    # Test a valid request returns proper time steps with a tracked token
    steps = [4, 8, 24]
    # Test with various steps
    for step in steps:
        res = client.get(
            "/chart-data",
            query_string={
                "token_symbol": "WBTC",
                "time_unit_in_hours": f"{step}",
            },
        )
        assert res.status_code == 200
        for row in res.json:
            for i in range(1, len(row)):
                ts1 = datetime.fromisoformat(row[i - 1][0])
                ts2 = datetime.fromisoformat(row[i][0])
                # Check if the time diff matches the expected time unit
                diff = ts2 - ts1
                assert diff == timedelta(hours=step)


def test_valid_request_w_untracked_token(client):
    # Test a valid request with an untracked token
    res = client.get(
        "/chart-data",
        query_string={"token_symbol": "ETH", "time_unit_in_hours": "24"},
    )
    assert res.status_code == 404
    assert res.json["error"] == "ETH is not currently tracked!"


def test_bad_requests(client):
    # Test bad requests with invalid steps
    steps = ["-1", "0", "0.5"]
    for step in steps:
        res = client.get(
            "/chart-data",
            query_string={
                "token_symbol": "ETH",
                "time_unit_in_hours": f"{step}",
            },
        )
        assert res.status_code == 400
        if step == "0.5":
            assert (
                "`time_unit_in_hours` must be an integer." in res.json["error"]
            )
        else:
            assert (
                "time_unit_in_hours` must be greater than 0."
                in res.json["error"]
            )

    # Test a bad request with missing values
    res = client.get(
        "/chart-data",
        query_string={"token_symbol": "", "time_unit_in_hours": "24"},
    )
    assert res.status_code == 400
    assert (
        res.json["error"]
        == "Both `token_symbol` and `time_unit_in_hours` query params are required."
    )


def test_server_error(client):
    # Test a scenario where the server raises an exception, e.g., invalid query params
    response = client.get(
        "/chart-data",
        query_string={"token": "WBTC", "time": "24"},
    )
    assert response.status_code == 500
    assert "An error occurred." in response.json["error"]
