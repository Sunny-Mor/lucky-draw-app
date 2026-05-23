from flask import Flask, jsonify
import redis
import psycopg2
import os
import time
import json
import threading
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

REDIS_HOST     = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT     = int(os.getenv("REDIS_PORT", 6379))
PG_HOST        = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT        = int(os.getenv("POSTGRES_PORT", 5432))
PG_DB          = os.getenv("POSTGRES_DB", "postgres")
PG_USER        = os.getenv("POSTGRES_USER", "postgres")
PG_PASS        = os.getenv("POSTGRES_PASSWORD", "postgres")
POLL_INTERVAL  = int(os.getenv("REDIS_POLL_INTERVAL", 5))

app = Flask(__name__)

logger.info("Redis → Postgres worker starting")

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
redis_client.ping()
logger.info("Connected to Redis")

pg_conn = psycopg2.connect(host=PG_HOST, port=PG_PORT, dbname=PG_DB, user=PG_USER, password=PG_PASS)
pg_conn.autocommit = True
logger.info("Connected to Postgres")

def create_table():
    with pg_conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS luckydraw (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                hostname TEXT,
                state TEXT NOT NULL DEFAULT 'not-participated',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
    logger.info("Table 'luckydraw' ensured")

create_table()

def redis_to_postgres_worker():
    logger.info("Worker thread started")
    while True:
        try:
            entries = redis_client.hgetall("lucky_draw_entries")
            if entries:
                logger.info(f"Found {len(entries)} Redis entries")
                with pg_conn.cursor() as cur:
                    for key, value in entries.items():
                        try:
                            data = json.loads(value)
                        except Exception:
                            logger.error(f"Invalid JSON for key {key}")
                            redis_client.hdel("lucky_draw_entries", key)
                            continue

                        name     = data.get("name")
                        phone    = data.get("phone")
                        hostname = data.get("hostname")

                        if not name or not phone:
                            redis_client.hdel("lucky_draw_entries", key)
                            continue

                        cur.execute(
                            "INSERT INTO luckydraw (name, phone, hostname) VALUES (%s, %s, %s);",
                            (name, phone, hostname)
                        )
                        redis_client.hdel("lucky_draw_entries", key)
                        logger.info(f"Synced: {name} | {phone}")
        except Exception:
            logger.exception("Worker loop error")

        time.sleep(POLL_INTERVAL)

threading.Thread(target=redis_to_postgres_worker, daemon=True).start()
logger.info("Worker thread launched")

@app.route("/health")
def health():
    return jsonify({"status": "UP"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, use_reloader=False)
