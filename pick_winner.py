from flask import Flask, render_template_string, redirect, url_for, request, session
import psycopg2
import os
import random
import socket
import logging
from datetime import datetime

# --------------------------------------------------
# Logging Setup
# --------------------------------------------------
LOG_DIR = "/var/log/luckydraw-app"
LOG_FILE = f"{LOG_DIR}/winner.log"

os.makedirs(LOG_DIR, exist_ok=True)

HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s {HOSTNAME} %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# --------------------------------------------------
# Config
# --------------------------------------------------
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
SECRET_KEY = os.getenv("SECRET_KEY", "luckydraw-secret")

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_DB   = os.getenv("POSTGRES_DB", "postgres")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

# --------------------------------------------------
# App
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = SECRET_KEY

logger.info("LuckyDraw application starting")

# --------------------------------------------------
# DB Connection
# --------------------------------------------------
pg_conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    dbname=PG_DB,
    user=PG_USER,
    password=PG_PASS
)
pg_conn.autocommit = False

# --------------------------------------------------
# Tables
# --------------------------------------------------
def init_db():
    with pg_conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS luckydraw_winner (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                picked_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
    pg_conn.commit()
    logger.info("Database initialized successfully")

init_db()

# --------------------------------------------------
# HTML
# --------------------------------------------------
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Lucky Draw Admin</title>
<style>
body { font-family: Arial; background: #0f172a; color: #fff; padding: 40px; }
.card { background: #1e293b; padding: 30px; border-radius: 15px; max-width: 650px; margin: auto; box-shadow: 0 0 25px rgba(0,0,0,.6); }
button { background: #22c55e; color: #000; padding: 14px 22px; border: none; font-size: 16px; border-radius: 8px; cursor: pointer; }
button:disabled { background: #64748b; cursor: not-allowed; }
.winner {
    font-size: 28px;
    margin: 15px 0;
    color: #22c55e;
    animation: reveal 1.2s ease-in-out;
}
.alert { color: #f87171; margin: 15px 0; }
table { width: 100%; margin-top: 20px; border-collapse: collapse; }
th, td { padding: 10px; border-bottom: 1px solid #334155; }
th { background: #020617; }
a { color: #38bdf8; text-decoration: none; }
</style>
</head>
<body>
<div class="card">
<h2>🎉 Lucky Draw Admin Panel</h2>
{% if not_logged %}
<form method="POST" action="/login">
    <input name="username" placeholder="Username" required><br><br>
    <input name="password" type="password" placeholder="Password" required><br><br>
    <button type="submit">Login</button>
</form>
{% else %}
{% if latest %}
<div class="winner">🏆 {{ latest.name }} ({{ latest.phone }})</div>
<p>Picked at: {{ latest.picked_at }}</p>
{% endif %}
{% if no_entries %}
<div class="alert">❌ No new entries available to pick a winner</div>
{% endif %}
<form method="POST" action="/pick">
    <button {% if no_entries %}disabled{% endif %}>Pick Winner</button>
</form>
<h3>📜 Winner History</h3>
<table>
<tr><th>Name</th><th>Phone</th><th>Picked At</th></tr>
{% for w in winners %}
<tr><td>{{ w.name }}</td><td>{{ w.phone }}</td><td>{{ w.picked_at }}</td></tr>
{% endfor %}
</table>
<br>
<a href="/logout">Logout</a>
{% endif %}
</div>
</body>
</html>
"""

# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    logged = session.get("logged_in", False)

    with pg_conn.cursor() as cur:
        cur.execute("""
            SELECT name, phone, picked_at
            FROM luckydraw_winner
            ORDER BY picked_at DESC;
        """)
        winners = cur.fetchall()

        cur.execute("""
            SELECT COUNT(*) FROM luckydraw
            WHERE state='not-participated';
        """)
        pending = cur.fetchone()[0]

    return render_template_string(
        HTML,
        winners=[{"name": w[0], "phone": w[1], "picked_at": w[2]} for w in winners],
        latest={"name": winners[0][0], "phone": winners[0][1], "picked_at": winners[0][2]} if winners else None,
        no_entries=pending == 0,
        not_logged=not logged
    )

@app.route("/login", methods=["POST"])
def login():
    if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
        session["logged_in"] = True
        logger.info("Admin login successful")
    else:
        logger.warning("Failed admin login attempt")
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    logger.info("Admin logged out")
    return redirect(url_for("index"))

@app.route("/pick", methods=["POST"])
def pick():
    if not session.get("logged_in"):
        logger.warning("Unauthorized pick attempt")
        return redirect(url_for("index"))

    try:
        with pg_conn.cursor() as cur:
            cur.execute("""
                SELECT id, name, phone
                FROM luckydraw
                WHERE state='not-participated'
                FOR UPDATE;
            """)
            rows = cur.fetchall()

            if not rows:
                pg_conn.rollback()
                logger.info("No participants available for draw")
                return redirect(url_for("index"))

            _, name, phone = random.choice(rows)

            cur.execute("""
                INSERT INTO luckydraw_winner (name, phone, picked_at)
                VALUES (%s, %s, %s);
            """, (name, phone, datetime.utcnow()))

            cur.execute("""
                UPDATE luckydraw
                SET state='participated'
                WHERE state='not-participated';
            """)

        pg_conn.commit()
        logger.info(f"Winner picked: name={name}, phone={phone}")

    except Exception as e:
        pg_conn.rollback()
        logger.exception("Error while picking winner")

    return redirect(url_for("index"))

@app.route("/health")
def health():
    logger.info("Health check accessed")
    return {"status": "UP"}

# --------------------------------------------------
# Main
# --------------------------------------------------
if __name__ == "__main__":
    logger.info("LuckyDraw app running on port 5000")
    app.run(host="0.0.0.0", port=5000)
