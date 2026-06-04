from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.features import CATEGORICAL_COLUMNS, NUMERIC_COLUMNS


def build_preprocessor() -> ColumnTransformer:
  return ColumnTransformer(
    transformers=[
      (
        "cat",
        OneHotEncoder(handle_unknown="ignore", sparse_output=False),
        CATEGORICAL_COLUMNS,
      ),
      ("num", StandardScaler(), NUMERIC_COLUMNS),
    ],
    remainder="drop",
    verbose_feature_names_out=False,
  )
