#!/usr/bin/env bash
#
# Read "<epoch> <process>: <message>" lines from stdin
# and POST them as a JSON array to an HTTP log-ingest service.
#
# Usage:
#     <producer> | ./log_inserter.sh <host> <port>
#
set -euo pipefail

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
die()  { printf 'ERROR: %s\n' "$*" >&2; exit 1; }
warn() { printf 'WARN:  %s\n' "$*" >&2; }

usage() {
    cat >&2 <<EOF
Usage: $(basename "$0") <host> <port>

Reads lines of the form:

    <epoch> <process>: <message>

from stdin and POSTs them to http://<host>:<port>/api/v1/logs as:

    [ { "application": "...", "event_time": <epoch>, "message": "..." } ]
EOF
    exit 1
}

# ---------------------------------------------------------------------------
# arguments
# ---------------------------------------------------------------------------
[[ $# -eq 2 ]] || usage
host=$1
port=$2

[[ $host =~ ^[A-Za-z0-9._-]+$ ]]                              || die "invalid host: $host"
[[ $port =~ ^[0-9]+$ && $port -ge 1 && $port -le 65535 ]]     || die "invalid port: $port"

url="http://${host}:${port}/api/v1/logs"

# dependencies
for cmd in curl jq; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done

# parse stdin into an in-memory array of JSON objects
entries=()
total=0

while IFS= read -r line || [[ -n "$line" ]]; do
    line=${line%$'\r'}                            # tolerate CRLF
    [[ -z ${line//[[:space:]]/} ]] && continue    # skip blank lines

    # <epoch> <process>: <message>
    if [[ ! $line =~ ^([0-9]+)[[:space:]]+(.+):[[:space:]]*(.*)$ ]]; then
        warn "skipping malformed line: $line"
        continue
    fi

    epoch=${BASH_REMATCH[1]}
    application=${BASH_REMATCH[2]}
    message=${BASH_REMATCH[3]}

    # trim trailing whitespace from the application name
    application=${application%"${application##*[![:space:]]}"}

    entries+=("$(jq -cn \
        --arg     application "$application" \
        --argjson event_time  "$epoch" \
        --arg     message     "$message" \
        '{application: $application, event_time: $event_time, message: $message}')")

    total=$((total + 1))
done

if (( total == 0 )); then
    warn "no valid entries read from stdin"
    exit 0
fi

# assemble payload (compact JSON array) fully in memory
payload=$(printf '%s\n' "${entries[@]}" | jq -cs '.')
[[ -n $payload ]] || die "failed to assemble JSON payload"

max_attempts=4
attempt=1

while (( attempt <= max_attempts )); do
    if resp=$(printf '%s' "$payload" | curl \
            --silent \
            --show-error \
            --write-out $'\n%{http_code}' \
            --connect-timeout 10 \
            --max-time 60 \
            --header 'Content-Type: application/json' \
            --request POST \
            --data-binary @- \
            "$url"); then

        # curl writes the -w output after the body, so the last line is the code
        http_code=${resp##*$'\n'}
        body=${resp%$'\n'*}

        if [[ $http_code == 2* ]]; then
            printf 'OK: sent %d entr%s to %s (HTTP %s)\n' \
                "$total" "$([[ $total -eq 1 ]] && echo y || echo ies)" \
                "$url" "$http_code"
            exit 0
        fi

        warn "HTTP $http_code from $url: $body"

        if [[ $http_code == 4* ]]; then
            die "server rejected the request (HTTP $http_code); not retrying"
        fi
    else
        rc=$?
        warn "curl failed (rc=$rc): ${resp:-<no response>}"
    fi

    attempt=$((attempt + 1))
    if (( attempt <= max_attempts )); then
        backoff=$(( 2 ** (attempt - 2) ))    # 1, 2, 4 seconds
        warn "retrying in ${backoff}s (attempt $attempt/$max_attempts)"
        sleep "$backoff"
    fi
done

die "failed to POST logs after $max_attempts attempts"