FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DB_HOST="localhost" \
    DB_PORT="5432" \
    DB_ADMIN_PASSWORD="" \
    POSTGRES_PASSWORD="" \
    POSTGRES_SUPERUSER=postgres 


# System deps (psql,)
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql \
    postgresql-contrib

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY utils ./utils
EXPOSE 8000
ENTRYPOINT ["python", "-m", "utils.bootstrap"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
