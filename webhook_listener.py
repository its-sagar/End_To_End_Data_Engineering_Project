from flask import Flask, request, jsonify
from config.config import AIRFLOW_USERNAME, AIRFLOW_PASSWORD
import requests
import hmac
import hashlib
import os

app = Flask(__name__)

# --- CONFIGURATION ---
AIRFLOW_DAG_ID = "etl_pipeline_dag"
AIRFLOW_URL = f"http://localhost:8080/api/v1/dags/{AIRFLOW_DAG_ID}/dagRuns"

# Set this to your GitHub webhook secret or leave as '' if unused
GITHUB_SECRET = os.getenv('GITHUB_SECRET', '')  # or hardcode: 'your_secret_here'

# --- VERIFY GITHUB SIGNATURE (OPTIONAL) ---
def verify_signature(data, signature):
    return True

# def verify_signature(data, signature):
#     if not GITHUB_SECRET:
#         return True  # Skip verification if no secret is set
#     if not signature:
#         return False
#     mac = hmac.new(GITHUB_SECRET.encode(), msg=data, digestmod=hashlib.sha256)
#     expected_signature = 'sha256=' + mac.hexdigest()
#     return hmac.compare_digest(expected_signature, signature)

# --- ROUTE ---
@app.route('/webhook', methods=['POST'])
def trigger_airflow_dag():
    signature = request.headers.get('X-Hub-Signature-256')
    if not verify_signature(request.data, signature):
        return jsonify({'error': 'Invalid signature'}), 403

    payload = {
        "conf": {},
        "dag_run_id": f"webhook__{request.json.get('after', 'manual')}"
    }

    try:
        response = requests.post(
            AIRFLOW_URL,
            auth=(AIRFLOW_USERNAME, AIRFLOW_PASSWORD),
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        return jsonify({
            "airflow_status": response.status_code,
            "airflow_response": response.json()
        }), response.status_code

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MAIN ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
