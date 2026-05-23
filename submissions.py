from flask import Flask, render_template_string
import psycopg2
import os
import socket
import logging

HOSTNAME = socket.gethostname()

logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s {HOSTNAME} %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = int(os.getenv("POSTGRES_PORT", 5432))
PG_DB   = os.getenv("POSTGRES_DB", "postgres")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "postgres")

app = Flask(__name__)

logger.info("Submissions application starting")

try:
    pg_conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
    logger.info(f"Connected to Postgres at {PG_HOST}:{PG_PORT}/{PG_DB}")
except Exception:
    logger.exception("Failed to connect to Postgres")
    raise

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Lucky Draw Submissions - Sunnymor</title>
    <style>
        body { font-family: Arial, sans-serif; background-color: #f2f2f2; text-align: center; margin-top: 30px; }
        table { width: 80%; margin: 0 auto; border-collapse: collapse; background-color: white; }
        th, td { border: 1px solid #ddd; padding: 8px; }
        th { background-color: #4CAF50; color: white; }
        tr:nth-child(even) { background-color: #f2f2f2; }
        #hostname { position: fixed; right: 10px; bottom: 10px; font-size: 0.8em; color: gray; }
        .empty { margin-top: 30px; font-size: 18px; color: #666; }
    </style>
</head>
<body>
<h2>Lucky Draw Submissions</h2>
{% if submissions %}
<table>
    <thead><tr><th>Name</th><th>Phone Number</th><th>Host Name</th></tr></thead>
    <tbody>
        {% for entry in submissions %}
        <tr><td>{{ entry.name }}</td><td>{{ entry.phone }}</td><td>{{ entry.hostname }}</td></tr>
        {% endfor %}
    </tbody>
</table>
{% else %}
<div class="empty">No active submissions available</div>
{% endif %}
<div id="hostname">Host: {{ hostname }}</div>
</body>
</html>
"""

@app.route("/submissions", methods=["GET"])
def view_submissions():
    submissions = []
    try:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT name, phone, hostname FROM luckydraw WHERE state = 'not-participated' ORDER BY created_at ASC;")
            for row in cur.fetchall():
                submissions.append({"name": row[0], "phone": row[1], "hostname": row[2]})
        logger.info(f"Fetched {len(submissions)} pending submissions")
    except Exception:
        logger.exception("Database query failed")

    return render_template_string(HTML_TEMPLATE, submissions=submissions, hostname=HOSTNAME)

@app.route("/health")
def health():
    return {"status": "UP"}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
