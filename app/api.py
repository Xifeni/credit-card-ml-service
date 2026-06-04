from flask import Flask, request, jsonify

from app.model_handler import load_models, predict, load_preprocessor
from app.request_logging import log_api_event, setup_logging

setup_logging()
app = Flask(__name__)
preprocessor = load_preprocessor()
models = load_models(preprocessor)


@app.route("/health", methods=["GET"])
def health():
  log_api_event("health_check", status="healthy")
  return jsonify({"status": "healthy"}), 200


@app.route("/predict", methods=["POST"])
def predict_endpoint():
  try:
    data = request.get_json()
    if not data:
      log_api_event("predict_error", error="empty_body", status_code=400)
      return jsonify({"error": "Empty request body"}), 400

    result = predict(models, data, preprocessor)
    log_api_event(
      "predict_success",
      model_version=result["model_version"],
      ab_assigned=result["ab_assigned"],
      ab_group=result["ab_group"],
      prediction=result["prediction"],
      probability=round(result["probability"], 6),
      customer_id=data.get("customer_id"),
    )
    return jsonify(result), 200

  except Exception as e:
    log_api_event("predict_error", error=str(e), status_code=400)
    return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=5000, debug=True)
