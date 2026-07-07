# Multi-stage: build stage installs dependencies into a venv, runtime
# stage copies only that venv + app code -- keeps pip's build cache and
# any transient build tooling out of the final image.
FROM python:3.11-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
# Unbuffered stdout/stderr so migration, seed, and app logs stream to
# Render's log tail immediately instead of sitting in Python's block
# buffer (only flushed on exit/buffer-full when stdout isn't a TTY).
ENV PYTHONUNBUFFERED=1

COPY --chown=appuser:appuser . .
RUN chmod +x entrypoint.sh

USER appuser

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

ENTRYPOINT ["./entrypoint.sh"]
