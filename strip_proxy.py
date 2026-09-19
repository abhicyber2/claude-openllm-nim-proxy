from flask import Flask, request, Response, jsonify
import requests, sqlite3, os, uuid, re
from datetime import datetime

app = Flask(__name__)
LITELLM_URL = "http://localhost:4000"
DB_PATH = "/opt/nim-proxy/usage.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS api_keys (
        key TEXT PRIMARY KEY, customer_id TEXT, plan TEXT,
        monthly_limit INTEGER, requests_used INTEGER DEFAULT 0, created_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS usage_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, api_key TEXT,
        timestamp TEXT, model TEXT, status INTEGER)""")
    conn.commit()
    conn.close()

init_db()

def get_customer(api_key):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT * FROM api_keys WHERE key = ?", (api_key,)).fetchone()
    conn.close()
    return row

def log_usage(api_key, model, status):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO usage_log VALUES (NULL, ?, ?, ?, ?)",
        (api_key, datetime.now().isoformat(), model, status))
    conn.execute("UPDATE api_keys SET requests_used = requests_used + 1 WHERE key = ?", (api_key,))
    conn.commit()
    conn.close()

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy"})

@app.route("/v1/messages", methods=["POST"])
def proxy():
    api_key = request.headers.get("x-api-key") or \
              request.headers.get("Authorization", "").replace("Bearer ", "")
    customer = get_customer(api_key)
    if not customer:
        return jsonify({"error": "Unauthorized"}), 401
    _, customer_id, plan, monthly_limit, requests_used, _ = customer
    if requests_used >= monthly_limit:
        return jsonify({"error": "Monthly limit exceeded"}), 429
    data = request.get_json()

    # LOG RAW MODEL NAME for debugging
    raw_model = data.get("model", "unknown")
    print(f"RAW MODEL RECEIVED: {repr(raw_model)}", flush=True)

    for param in ["output_config", "anthropic_beta", "betas"]:
        data.pop(param, None)

    # Aggressively clean model name
    clean_model = re.sub(r'\x1b\[[0-9;]*m?', '', raw_model)
    clean_model = re.sub(r'\[[0-9;]*m?', '', clean_model)
    clean_model = re.sub(r'[^a-zA-Z0-9\-\.]', '', clean_model)
    clean_model = clean_model.strip().lower()

    print(f"CLEAN MODEL: {repr(clean_model)}", flush=True)

    if "opus" in clean_model:
        data["model"] = "claude-opus"
    elif "haiku" in clean_model:
        data["model"] = "claude-haiku"
    else:
        data["model"] = "claude-sonnet"

    print(f"FINAL MODEL: {data['model']}", flush=True)

    model = data.get("model", "unknown")
    resp = requests.post(f"{LITELLM_URL}/v1/messages", json=data,
        headers={k: v for k, v in request.headers if k != "Host"}, stream=True)
    log_usage(api_key, model, resp.status_code)
    return Response(resp.iter_content(chunk_size=1024),
        status=resp.status_code, content_type=resp.headers.get("content-type"))

@app.route("/usage", methods=["GET"])
def usage():
    api_key = request.headers.get("x-api-key")
    customer = get_customer(api_key)
    if not customer:
        return jsonify({"error": "Unauthorized"}), 401
    _, customer_id, plan, monthly_limit, requests_used, created_at = customer
    return jsonify({"customer_id": customer_id, "plan": plan,
        "requests_used": requests_used, "monthly_limit": monthly_limit,
        "remaining": monthly_limit - requests_used})

@app.route("/admin/create-key", methods=["POST"])
def create_key():
    admin_key = request.headers.get("x-admin-key")
    if admin_key != os.environ.get("ADMIN_KEY"):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json()
    new_key = "nim-" + str(uuid.uuid4())
    plan = data.get("plan", "starter")
    limits = {"starter": 5000, "team": 25000, "business": 100000}
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO api_keys VALUES (?, ?, ?, ?, 0, ?)",
        (new_key, data.get("customer_id"), plan,
         limits.get(plan, 5000), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"api_key": new_key, "plan": plan})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4001)
