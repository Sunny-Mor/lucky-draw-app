# ---- build stage ----
FROM python:3.11-slim AS builder
WORKDIR /build
COPY docker/pick-winner/requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---- runtime stage ----
FROM python:3.11-slim
WORKDIR /app

COPY --from=builder /install /usr/local

RUN useradd -r -u 1001 -s /sbin/nologin appuser
COPY pick_winner.py app.py
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", "app:app"]
