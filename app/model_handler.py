from pathlib import Path

import joblib
import pandas as pd

from app.ab_split import feature_payload, resolve_model_version
from app.features import FEATURE_COLUMNS

BASE_DIR = Path(__file__).resolve().parent.parent

MODEL_PATHS = {
  "v1": BASE_DIR / "models/logistic_regression_model.pkl",
  "v2": BASE_DIR / "models/random_forest_model.pkl",
}


def _expected_n_features(preprocessor) -> int:
  """Число признаков на выходе препроцессора (после OneHot + scaling)."""
  if hasattr(preprocessor, "n_features_out_"):
    return preprocessor.n_features_out_
  sample = _build_feature_frame({col: 0 for col in FEATURE_COLUMNS})
  return preprocessor.transform(sample).shape[1]


def load_models(preprocessor=None):
  if preprocessor is None:
    preprocessor = load_preprocessor()
  expected = _expected_n_features(preprocessor)

  models = {}
  for version, path in MODEL_PATHS.items():
    if not path.exists():
      raise FileNotFoundError(f"Model artifact missing: {path}")
    model = joblib.load(path)
    model_n = getattr(model, "n_features_in_", None)
    if model_n is not None and model_n != expected:
      raise RuntimeError(
        f"{version} expects {model_n} features, preprocessor has {expected}. "
        "Re-run: python models/train_model.py"
      )
    models[version] = model
  return models


def load_preprocessor():
  return joblib.load(BASE_DIR / "models/preprocessor.pkl")


def _build_feature_frame(data: dict) -> pd.DataFrame:
  features = feature_payload(data)
  missing = [col for col in FEATURE_COLUMNS if col not in features]
  if missing:
    raise ValueError(f"Missing features: {missing}")

  row = {col: features[col] for col in FEATURE_COLUMNS}
  return pd.DataFrame([row], columns=FEATURE_COLUMNS)


def predict(models, data, preprocessor):
  routing = resolve_model_version(data, available_versions=tuple(models.keys()))
  model_version = routing["model_version"]
  model = models[model_version]

  input_df = _build_feature_frame(data)
  x_scaled = preprocessor.transform(input_df)
  prediction = int(model.predict(x_scaled)[0])
  probability = float(model.predict_proba(x_scaled)[0][1])

  return {
    "prediction": prediction,
    "probability": probability,
    "model_version": model_version,
    "ab_assigned": routing["ab_assigned"],
    "ab_group": routing["ab_group"],
  }
