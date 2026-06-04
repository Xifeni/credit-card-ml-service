import pytest

from app.ab_split import assign_version, resolve_model_version
from app.api import app


def test_assign_version_is_deterministic():
  assert assign_version("user-42", 0.5) == assign_version("user-42", 0.5)


def test_assign_version_respects_ratio():
  v2_count = sum(1 for i in range(1000) if assign_version(f"id-{i}", 0.5) == "v2")
  assert 400 <= v2_count <= 600


def test_resolve_explicit_override():
  result = resolve_model_version({"model_version": "v2", "customer_id": "1"})
  assert result["model_version"] == "v2"
  assert result["ab_assigned"] is False


def test_resolve_autosplit_when_enabled(monkeypatch):
  monkeypatch.setenv("AB_TEST_ENABLED", "true")
  monkeypatch.setenv("AB_SPLIT_RATIO", "0.5")
  a = resolve_model_version({"customer_id": "stable-user-100"})
  b = resolve_model_version({"customer_id": "stable-user-100"})
  assert a == b
  assert a["ab_assigned"] is True
  assert a["ab_group"] in ("A", "B")


def test_resolve_requires_subject_when_enabled(monkeypatch):
  monkeypatch.setenv("AB_TEST_ENABLED", "true")
  with pytest.raises(ValueError, match="A/B test enabled"):
    resolve_model_version({"LIMIT_BAL": 1})


@pytest.fixture
def client():
  app.config["TESTING"] = True
  with app.test_client() as client:
    yield client


def _feature_payload(**extra):
  base = {
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
    "PAY_AMT6": 0,
  }
  base.update(extra)
  return base


def test_predict_autosplit_via_api(monkeypatch, client):
  monkeypatch.setenv("AB_TEST_ENABLED", "true")
  payload = _feature_payload(customer_id="client-777")

  response = client.post("/predict", json=payload)
  assert response.status_code == 200
  data = response.get_json()
  assert data["ab_assigned"] is True
  assert data["ab_group"] in ("A", "B")
  assert data["model_version"] == ("v2" if data["ab_group"] == "B" else "v1")

  repeat = client.post("/predict", json=payload).get_json()
  assert repeat["model_version"] == data["model_version"]
  assert repeat["ab_group"] == data["ab_group"]


def test_predict_explicit_version_skips_autosplit(monkeypatch, client):
  monkeypatch.setenv("AB_TEST_ENABLED", "true")
  payload = _feature_payload(model_version="v2")

  response = client.post("/predict", json=payload)
  assert response.status_code == 200
  data = response.get_json()
  assert data["model_version"] == "v2"
  assert data["ab_assigned"] is False
  assert data["ab_group"] == "B"
