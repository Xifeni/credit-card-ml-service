from pathlib import Path
import sys

import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score
from sklearn.model_selection import train_test_split
import joblib

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.features import FEATURE_COLUMNS  # noqa: E402
from app.preprocessing import build_preprocessor  # noqa: E402

MODELS_DIR = BASE_DIR / "models"
TARGET = "default.payment.next.month"
DROP_COLUMNS = {"ID", TARGET}
RANDOM_STATE = 42


def dataset_path() -> Path:
  for candidate in (
    BASE_DIR / "dataset" / "UCI_Credit_Card.csv",
    BASE_DIR / "data" / "raw" / "UCI_Credit_Card.csv",
  ):
    if candidate.exists():
      return candidate
  raise FileNotFoundError(
    "Dataset not found. Place UCI_Credit_Card.csv in dataset/ or data/raw/"
  )


def load_dataset() -> tuple[pd.DataFrame, pd.Series]:
  path = dataset_path()
  df = pd.read_csv(path)
  if TARGET not in df.columns:
    raise ValueError(f"Expected target column '{TARGET}' in {path}")

  y = df[TARGET].astype(int)
  missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
  if missing:
    raise ValueError(f"Dataset missing columns: {missing}")
  x = df[FEATURE_COLUMNS]
  return x, y


def main():
  x, y = load_dataset()
  x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
  )

  preprocessor = build_preprocessor()
  x_train_scaled = preprocessor.fit_transform(x_train)
  x_test_scaled = preprocessor.transform(x_test)
  print(
    f"Preprocessor: {preprocessor.__class__.__name__}, "
    f"input features={len(FEATURE_COLUMNS)}, "
    f"output features={preprocessor.transform(x_train[:1]).shape[1]}"
  )

  models = {
    "v1": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
    "v2": RandomForestClassifier(
      n_estimators=100, random_state=RANDOM_STATE, n_jobs=1
    ),
  }
  artifact_names = {
    "v1": "logistic_regression_model.pkl",
    "v2": "random_forest_model.pkl",
  }

  MODELS_DIR.mkdir(parents=True, exist_ok=True)
  joblib.dump(preprocessor, MODELS_DIR / "preprocessor.pkl")
  print(f"Saved preprocessor -> {MODELS_DIR / 'preprocessor.pkl'}")

  for version, estimator in models.items():
    estimator.fit(x_train_scaled, y_train)
    y_pred = estimator.predict(x_test_scaled)
    f1 = f1_score(y_test, y_pred)
    print(f"\n=== {version} ({estimator.__class__.__name__}) F1={f1:.4f} ===")
    print(classification_report(y_test, y_pred))

    out_path = MODELS_DIR / artifact_names[version]
    joblib.dump(estimator, out_path)
    print(f"Saved -> {out_path}")

if __name__ == "__main__":
  main()
