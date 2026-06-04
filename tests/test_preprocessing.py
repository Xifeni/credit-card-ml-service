import joblib
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

from app.features import CATEGORICAL_COLUMNS, FEATURE_COLUMNS
from app.preprocessing import build_preprocessor


def test_build_preprocessor_structure():
  prep = build_preprocessor()
  assert isinstance(prep, ColumnTransformer)
  steps = {name: transformer for name, transformer, _ in prep.transformers}
  assert isinstance(steps["cat"], OneHotEncoder)
  assert steps["num"].__class__.__name__ == "StandardScaler"


def test_saved_preprocessor_is_column_transformer():
  prep = joblib.load("models/preprocessor.pkl")
  assert isinstance(prep, ColumnTransformer)
  assert list(prep.feature_names_in_) == FEATURE_COLUMNS
  assert set(prep.named_transformers_["cat"].feature_names_in_) == set(
    CATEGORICAL_COLUMNS
  )
