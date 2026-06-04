import json
import pytest

from app.api import app

@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client

def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert "status" in data
    assert data["status"] == "healthy"


def test_predict_success(client):
    payload = {
        "LIMIT_BAL": 20000,
        "SEX": 2,
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": 24,
        "PAY_0": 2,
        "PAY_2": 2,
        "PAY_3": -1,
        "PAY_4": -1,
        "PAY_5": -2,
        "PAY_6": -2,
        "BILL_AMT1": 3913,
        "BILL_AMT2": 3102,
        "BILL_AMT3": 689,
        "BILL_AMT4": 0,
        "BILL_AMT5": 0,
        "BILL_AMT6": 0,
        "PAY_AMT1": 0,
        "PAY_AMT2": 689,
        "PAY_AMT3": 0,
        "PAY_AMT4": 0,
        "PAY_AMT5": 0,
        "PAY_AMT6": 0
    }

    response = client.post(
        "/predict",
        data=json.dumps(payload),
        content_type="application/json"
    )
    print(response.get_json())
    assert response.status_code == 200

    data = response.get_json()
    assert data is not None
    assert "prediction" in data
    assert "probability" in data
    assert "model_version" in data
    assert data["model_version"] == "v1"
    assert data["ab_assigned"] is False

    assert data["prediction"] in [0, 1]
    assert isinstance(data["probability"], (float, int))
    assert 0.0 <= float(data["probability"]) <= 1.0


def test_predict_empty_json(client):
    response = client.post(
        "/predict",
        data=json.dumps({}),
        content_type="application/json"
    )

    assert response.status_code in [400, 422]

    data = response.get_json()
    assert data is not None
    assert "error" in data


def test_predict_missing_fields(client):
    payload = {
        "LIMIT_BAL": 20000,
        "SEX": 2
    }

    response = client.post(
        "/predict",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code in [400, 422]

    data = response.get_json()
    assert data is not None
    assert "error" in data

def test_predict_success_v2(client):
    payload = {
        "model_version": "v2",
        "LIMIT_BAL": 20000,
        "SEX": 2,
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": 24,
        "PAY_0": 2,
        "PAY_2": 2,
        "PAY_3": -1,
        "PAY_4": -1,
        "PAY_5": -2,
        "PAY_6": -2,
        "BILL_AMT1": 3913,
        "BILL_AMT2": 3102,
        "BILL_AMT3": 689,
        "BILL_AMT4": 0,
        "BILL_AMT5": 0,
        "BILL_AMT6": 0,
        "PAY_AMT1": 0,
        "PAY_AMT2": 689,
        "PAY_AMT3": 0,
        "PAY_AMT4": 0,
        "PAY_AMT5": 0,
        "PAY_AMT6": 0
    }

    response = client.post(
        "/predict",
        json=payload
    )

    assert response.status_code == 200, response.get_json()

    data = response.get_json()
    assert data is not None
    assert "prediction" in data
    assert "probability" in data
    assert "model_version" in data
    assert data["model_version"] == "v2"
    assert data["ab_assigned"] is False
    assert data["ab_group"] == "B"
    assert data["prediction"] in [0, 1]
    assert 0.0 <= float(data["probability"]) <= 1.0


def test_predict_invalid_model_version(client):
    payload = {
        "model_version": "v3",
        "LIMIT_BAL": 20000,
        "SEX": 2,
        "EDUCATION": 2,
        "MARRIAGE": 1,
        "AGE": 24,
        "PAY_0": 2,
        "PAY_2": 2,
        "PAY_3": -1,
        "PAY_4": -1,
        "PAY_5": -2,
        "PAY_6": -2,
        "BILL_AMT1": 3913,
        "BILL_AMT2": 3102,
        "BILL_AMT3": 689,
        "BILL_AMT4": 0,
        "BILL_AMT5": 0,
        "BILL_AMT6": 0,
        "PAY_AMT1": 0,
        "PAY_AMT2": 689,
        "PAY_AMT3": 0,
        "PAY_AMT4": 0,
        "PAY_AMT5": 0,
        "PAY_AMT6": 0
    }

    response = client.post(
        "/predict",
        json=payload
    )

    assert response.status_code == 400

    data = response.get_json()
    assert data is not None
    assert "error" in data
    assert "Invalid model_version" in data["error"]