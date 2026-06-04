import hashlib
import os

VALID_VERSIONS = ("v1", "v2")
SERVICE_FIELDS = frozenset({
  "model_version",
  "customer_id",
  "request_id",
  "ID",
  "id",
})


def ab_config():
  enabled = os.getenv("AB_TEST_ENABLED", "false").lower() in ("1", "true", "yes")
  try:
    split_ratio = float(os.getenv("AB_SPLIT_RATIO", "0.5"))
  except ValueError:
    split_ratio = 0.5
  split_ratio = min(max(split_ratio, 0.0), 1.0)
  hash_field = os.getenv("AB_HASH_FIELD", "customer_id")
  return {
    "enabled": enabled,
    "split_ratio": split_ratio,
    "hash_field": hash_field,
  }


def assign_version(subject_id: str, split_ratio: float) -> str:
  digest = hashlib.sha256(str(subject_id).encode()).hexdigest()
  bucket = int(digest[:8], 16) % 100
  threshold = int(split_ratio * 100)
  return "v2" if bucket < threshold else "v1"


def ab_group_for_version(model_version: str) -> str:
  return "B" if model_version == "v2" else "A"


def _subject_id(data: dict, hash_field: str) -> str | None:
  for key in (hash_field, "customer_id", "request_id", "ID", "id"):
    value = data.get(key)
    if value is not None and str(value).strip() != "":
      return str(value)
  return None


def resolve_model_version(data: dict, available_versions: tuple[str, ...] = VALID_VERSIONS):
  config = ab_config()
  explicit = data.get("model_version")

  if explicit is not None:
    explicit = str(explicit).strip()
    if explicit not in available_versions:
      raise ValueError(f"Invalid model_version: {explicit}")
    return {
      "model_version": explicit,
      "ab_assigned": False,
      "ab_group": ab_group_for_version(explicit),
    }

  if config["enabled"]:
    subject_id = _subject_id(data, config["hash_field"])
    if subject_id is None:
      raise ValueError(
        f"A/B test enabled: provide '{config['hash_field']}' "
        "(or customer_id / request_id / ID) for traffic split"
      )
    version = assign_version(subject_id, config["split_ratio"])
    return {
      "model_version": version,
      "ab_assigned": True,
      "ab_group": ab_group_for_version(version),
    }

  return {
    "model_version": "v1",
    "ab_assigned": False,
    "ab_group": "A",
  }


def feature_payload(data: dict) -> dict:
  return {k: v for k, v in data.items() if k not in SERVICE_FIELDS}
