#!/usr/bin/env bash
#
# Send a DELETE request with query parameters.
#
# Usage: ./delete-logs.sh <host> <port> <application> <from> <to>
#
#   host        - target hostname or IP (e.g. example.com)
#   port        - target port (e.g. 8080)
#   application - application name
#   from        - datetime (RFC3339) or epoch seconds
#   to          - datetime (RFC3339) or epoch seconds
#
set -euo pipefail

usage() {
    cat <<EOF
Usage: $(basename "$0") <host> <port> <application> <from> <to>

Arguments:
  host         Target host (hostname or IP)
  port         Target port
  application  Application name
  from         Start time (RFC3339 datetime or epoch seconds)
  to           End time   (RFC3339 datetime or epoch seconds)

Example:
  $(basename "$0") api.example.com 8080 my-app "2024-01-01T00:00:00Z" 1704067200
EOF
}

die() {
    echo "Error: $*" >&2
    exit 1
}

# ---- Argument validation ----------------------------------------------------
if [[ $# -ne 5 ]]; then
    usage >&2
    exit 2
fi

host="$1"
port="$2"
application="$3"
from="$4"
to="$5"

[[ -n "$host" ]]         || die "host must not be empty"
[[ "$port" =~ ^[0-9]+$ ]] || die "port must be numeric (got: '$port')"
(( port >= 1 && port <= 65535 )) || die "port must be in range 1-65535 (got: $port)"
[[ -n "$application" ]]  || die "application must not be empty"
[[ -n "$from" ]]         || die "from must not be empty"
[[ -n "$to" ]]           || die "to must not be empty"

# ---- Dependency checks ------------------------------------------------------
for cmd in curl; do
    command -v "$cmd" >/dev/null 2>&1 || die "required command not found: $cmd"
done

url="http://${host}:${port}/api/v1/logs"

# ---- Send request -----------------------------------------------------------
# --get forces query-string mode; --data-urlencode encodes each key=value
# properly (spaces, colons, etc. in datetimes are handled for us).
tmp_body="$(mktemp)"
trap 'rm -f "$tmp_body"' EXIT

set +e
http_code="$(curl \
    --silent --show-error \
    --connect-timeout 10 \
    --max-time 60 \
    --request DELETE \
    --get \
    --header 'Accept: application/json' \
    --data-urlencode "application=${application}" \
    --data-urlencode "from=${from}" \
    --data-urlencode "to=${to}" \
    --output "$tmp_body" \
    --write-out '%{http_code}' \
    "$url")"
curl_rc=$?
set -e

body="$(cat "$tmp_body" 2>/dev/null || true)"

if (( curl_rc != 0 )); then
    case "$curl_rc" in
        6)  die "could not resolve host '$host' (curl exit $curl_rc)" ;;
        7)  die "failed to connect to ${host}:${port} (curl exit $curl_rc)" ;;
        28) die "request timed out (curl exit $curl_rc)" ;;
        35) die "TLS handshake failed (curl exit $curl_rc)" ;;
        *)  die "curl failed with exit code $curl_rc${body:+: $body}" ;;
    esac
fi

if [[ ! "$http_code" =~ ^2 ]]; then
    echo "HTTP ${http_code} from ${url}" >&2
    [[ -n "$body" ]] && echo "$body" >&2
    exit 1
fi

echo "Success (HTTP ${http_code})"
[[ -n "$body" ]] && echo "$body"

exit 0
