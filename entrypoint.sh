#!/bin/sh
set -e

# Bootstrap phase
echo "Running bootstrap..."
#python -m utils.bootstrap
# wait a beat for the socket dir
mkdir -p /var/run/postgresql

# echo "Starting PostgreSQL from $PGDATA ..."
# pg_ctl -D "$PGDATA" \
#     -o "-c listen_addresses=127.0.0.1 -c port=${DB_PORT} -c unix_socket_directories=/var/run/postgresql" \
#     -l "$PGDATA/postgres.log" \
#     -w -t 60 \
#     start

# Wait until it accepts queries (pg_ctl -w already does this, but be explicit)
until pg_isready -h 127.0.0.1 -p "${DB_PORT}" -U "${POSTGRES_USER}" >/dev/null 2>&1; do
    sleep 0.5
done
echo "PostgreSQL is ready."

# Hand off to main process (exec so it becomes PID 1)
echo "Starting main service..."
uvicorn app.main:app --host 0.0.0.0 --port 8000