FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    libpq-dev \
    gcc \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

EXPOSE 8000

# Automatyczne tworzenie i stosowanie migracji
CMD sh -c "\
    echo '⏳ Waiting for database...' && \
    while ! nc -z db 5432; do sleep 1; done && \
    echo '✅ Database ready!' && \
    echo '' && \
    echo '⏳ Creating migrations...' && \
    python manage.py makemigrations && \
    echo '✅ Migrations created!' && \
    echo '' && \
    echo '⏳ Applying migrations...' && \
    python manage.py migrate && \
    echo '✅ Migrations applied!' && \
    echo '' && \
    python manage.py collectstatic --noinput && \
    echo '' && \
    echo '🚀 Starting server...' && \
    python manage.py runserver 0.0.0.0:8000"