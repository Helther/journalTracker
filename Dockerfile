FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PGDATA=/var/lib/postgresql/data \
    DB_HOST="localhost" \
    DB_PORT="5432" \
    POSTGRES_USER="postgres" \
    POSTGRES_PASSWORD="postgres" \
    POSTGRES_DB="log_service_db"

# System deps (psql,)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql \
    postgresql-contrib

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY utils ./utils
COPY entrypoint.sh .
RUN ["chmod", "+x", "/app/entrypoint.sh"]

RUN mkdir -p "$PGDATA" /var/run/postgresql \
 && chown -R postgres:postgres "$PGDATA" /var/run/postgresql /app


EXPOSE 8000
CMD ["/app/entrypoint.sh"]
