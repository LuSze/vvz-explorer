FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only torch first (saves ~3GB vs CUDA build)
RUN pip install --no-cache-dir --default-timeout=120 \
    --index-url https://download.pytorch.org/whl/cpu \
    torch

COPY requirements.txt .
RUN pip install --no-cache-dir --default-timeout=120 -r requirements.txt

COPY . .

# Collect static files
ENV DJANGO_SETTINGS_MODULE=backend.settings.prod
ARG DJANGO_SECRET_KEY=dummy-build-key
ENV DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]