from flask import Flask, render_template_string, request, redirect, url_for, flash
import redis
import os
import socket
import json
import logging

HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s {HOSTNAME} %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
except Exception:
    logger.exception("Failed to connect to Redis")
    raise

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "luckydraw-secret")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lucky Draw - SUNNYMOR</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f2f2f2; text-align: center; margin-top: 50px; }
        form { display: inline-block; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
        input[type="text"], input[type="tel"] { width: 100%; margin-bottom: 10px; padding: 8px; }
        button { background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background-color: #45a049; }
    </style>
</head>
<body>
    <h2>LUCKY DRAW - SUNNYMOR</h2>
    <form action="{{ url_for('participate') }}" method="post">
        <input type="text" name="name" placeholder="Enter your Name" required><br>
        <input type="tel" name="phone" placeholder="Enter your Phone Number" required pattern="[0-9]{10,15}"><br>
        <button type="submit">Participate</button>
    </form>
    {% with messages = get_flashed_messages() %}
        {% if messages %}
            <ul style="color: green;">
            {% for message in messages %}
                <li>{{ message }}</li>
            {% endfor %}
            </ul>
        {% endif %}
    {% endwith %}
</body>
</html>
"""

@app.route("/participate", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/participate", methods=["POST"])
def participate():
    name = request.form.get("name")
    phone = request.form.get("phone")

    if not name or not phone:
        return redirect(url_for("index"))

    try:
        r.hset("lucky_draw_entries", name, json.dumps({"name": name, "phone": phone, "hostname": HOSTNAME}))
        logger.info(f"Registered participant: name={name}, phone={phone}")
        flash(f"{name} ({phone}) registered successfully from {HOSTNAME}!")
    except Exception:
        logger.exception(f"Failed to register participant: name={name}")

    return redirect(url_for("index"))

@app.route("/health")
def health():
    return {"status": "UP"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
