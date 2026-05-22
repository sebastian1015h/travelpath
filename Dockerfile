# ─────────────────────────────────────────────────────────────────────────────
# STAGE 1 — builder
# Instala dependencias en un venv aislado.
# Esta capa nunca llega a producción, por eso puede tener gcc y compiladores.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11.9-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# STAGE 2 — runtime
# Imagen final mínima: solo el venv compilado + código fuente.
# Sin gcc, sin pip, sin archivos de build → imagen ~60% más pequeña.
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11.9-slim AS runtime

WORKDIR /app

# Usuario sin privilegios root (buena práctica de seguridad)
RUN useradd --no-create-home --shell /bin/false appuser

# Copia el entorno virtual compilado del builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copia el código fuente
COPY --chown=appuser:appuser . .

# Cambia al usuario sin privilegios
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

CMD ["gunicorn", "app:app", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
