#!/usr/bin/env bash
#
# fetch_logs.sh - print formatted log entries from the HTTP log service.
#
# Usage: ./fetch_logs.sh <host> <port> <application>
#
# Output format: "<time> <process>: <message>"

set -euo pipefail

usage() {
    echo "Usage: $0 <host> <port> <application>" >&2
    exit 64  # EX_USAGE
}

# argument validation
if [[ $# -ne 3 ]]; then
    usage
fi

HOST="$1"
PORT="$2"
APPLICATION="$3"

if [[ -z "$HOST" || -z "$PORT" || -z "$APPLICATION" ]]; then
    echo "Error: host, port and application must be non-empty." >&2
    usage
fi

if ! [[ "$PORT" =~ ^[0-9]+$ ]] || (( PORT < 1 || PORT > 65535 )); then
    echo "Error: invalid port '$PORT'." >&2
    exit 64
fi

# dependency checks
for cmd in curl jq; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
        echo "Error: required command '$cmd' not found in PATH." >&2
        exit 69  # EX_UNAVAILABLE
    fi
done

# prepare request 
URL="http://${HOST}:${PORT}/api/v1/logs"

# perform request
if ! response=$(curl -sS -G \
        --connect-timeout 5 \
        --max-time 30 \
        -w '\n%{http_code}' \
        --data-urlencode "application=${APPLICATION}" \
        "$URL"); then
    rc=$?
    echo "Error: request to ${URL} failed (curl exit code ${rc})." >&2
    case "$rc" in
        6)  echo "       Could not resolve host '${HOST}'." >&2 ;;
        7)  echo "       Could not connect to ${HOST}:${PORT}." >&2 ;;
        28) echo "       Request timed out." >&2 ;;
    esac
    exit 1
fi

# Split response into body and status code
http_status="${response##*$'\n'}"
body="${response%$'\n'*}"

# validate HTTP status
if [[ ! "$http_status" =~ ^2[0-9][0-9]$ ]]; then
    echo "Error: server returned HTTP $http_status." >&2
    if [[ -n "$body" ]]; then
        echo "Response body: $body" >&2
    fi
    exit 1
fi

# validate response body
if [[ -z "$body" ]]; then
    echo "Error: empty response body (HTTP ${http_status})." >&2
    exit 1
fi

if ! jq -e . >/dev/null 2>&1 <<<"$body"; then
    echo "Error: response is not valid JSON (HTTP ${http_status})." >&2
    exit 1
fi

if ! jq -e 'has("items") and (.items | type == "array")' >/dev/null 2>&1 <<<"$body"; then
    echo "Error: unexpected response schema - 'items' array not found." >&2
    exit 1
fi

# format and print
jq -r '
    .items[]
    | [
        (.event_time // "?"),
        ((.application // "?") + ":"),
        (.message // "")
      ]
    | "\(.[0]) \(.[1]) \(.[2])"
' <<<"$body"