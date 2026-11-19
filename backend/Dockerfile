#FROM python:3.12-slim
#FROM dhi.io/python:3.15.2-alpine
#ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
#WORKDIR /app
#COPY requirements.txt .
#RUN pip install --no-cache-dir -r requirements.txt
#COPY . .
#RUN useradd --create-home appuser
#USER appuser
#EXPOSE 8000
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]

# syntax=docker/dockerfile:1

# ---------- Etapa 1: instalar dependencias (variante -dev: shell, pip, apk) ----------
FROM dhi.io/python:3.13-alpine3.23-dev AS build
ENV PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------- Etapa 2: runtime (sin shell, sin gestor de paquetes, usuario nonroot 65532) ----------
# Debe ser la MISMA versión de Python que la etapa 1 (el venv enlaza al intérprete).
FROM dhi.io/python:3.13-alpine3.23
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH"
WORKDIR /app
COPY --from=build /app/venv /app/venv

# Se copia solo el código necesario (nunca .env, scripts ni archivos de despliegue)
COPY main.py ./
COPY core ./core
COPY models ./models
COPY routers ./routers
COPY schemas ./schemas
COPY services ./services

EXPOSE 8000
# --forwarded-allow-ips=*: seguro porque el puerto 8000 NO se publica; solo Traefik (red "proxy") llega a él.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]