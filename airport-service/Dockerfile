FROM python:3.11-slim AS builder
WORKDIR /app
RUN python -m venv /venv
COPY requirements.txt .
RUN /venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime
WORKDIR /app
COPY --from=builder /venv /venv
COPY . .
RUN useradd -m appuser && chown -R appuser /app
USER appuser
ENV PATH="/venv/bin:$PATH"
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/health')"
CMD ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "2", "--timeout", "120", "app:app"]
