# Academy API image. Build from the repo root:
#   docker build -f server/Dockerfile .
FROM python:3.12-slim

WORKDIR /app

RUN useradd --create-home --uid 1000 academy \
    && mkdir -p /cache/jax /app/results/records \
    && chown -R academy:academy /cache /app

COPY requirements.txt /app/requirements.txt
COPY server/requirements.txt /app/server/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt -r /app/server/requirements.txt

COPY src /app/src
COPY server /app/server
RUN chown -R academy:academy /app

USER academy
ENV PYTHONPATH=/app \
    MPLCONFIGDIR=/tmp/mpl \
    JAX_COMPILATION_CACHE_DIR=/cache/jax \
    ACADEMY_WARMUP=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health')"

CMD ["uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
