#!/usr/bin/env bash
#
# journal_tail.sh — print the last N entries from journalctl as
# "<epoch> <process>: <message>".
#
# Usage: ./journal-tail.sh N

set -uo pipefail

prog=$(basename "$0")

usage() {
    printf 'Usage: %s N\n' "$prog" >&2
    printf '  N  Number of most recent journalctl entries to print.\n' >&2
    exit 1
}

# Argument validation 
[[ $# -eq 1 ]] || usage
N="$1"

if [[ ! "$N" =~ ^[0-9]+$ ]]; then
    printf '%s: error: N must be a non-negative integer (got %q)\n' "$prog" "$N" >&2
    exit 1
fi

(( N == 0 )) && exit 0

# Dependency checks
if ! command -v journalctl >/dev/null 2>&1; then
    printf '%s: error: journalctl not found in PATH\n' "$prog" >&2
    exit 127
fi

# Temp file to capture journalctl's stderr separately from stdout.
err_file=$(mktemp) || { printf '%s: error: cannot create temp file\n' "$prog" >&2; exit 1; }
trap 'rm -f "$err_file"' EXIT

# Fetch the log
output=""
if ! output=$(journalctl -n "$N" --no-pager -o short-iso 2>"$err_file"); then
    rc=$?
    printf '%s: error: journalctl exited with status %d\n' "$prog" "$rc" >&2
    if [[ -s "$err_file" ]]; then
        printf '%s: journalctl stderr follows:\n' "$prog" >&2
        sed 's/^/    /' "$err_file" >&2
    fi
    exit "$rc"
fi

# Surface warnings even when journalctl succeeded.
if [[ -s "$err_file" ]]; then
    printf '%s: journalctl reported (stderr):\n' "$prog" >&2
    sed 's/^/    /' "$err_file" >&2
fi

if [[ -z "$output" ]]; then
    printf '%s: error: journalctl returned no entries (empty output)\n' "$prog" >&2
    exit 1
fi

# Parse and reformat
re='^([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?([+-][0-9]{2}:?[0-9]{2}|Z)?) ([^ ]+) ([^:]+): (.*)$'

while IFS= read -r line; do

    # Blank line.
    if [[ -z "$line" ]]; then
        continue
    fi

    # journalctl banner, e.g. "-- No entries --", "-- Logs begin at ... --".
    if [[ "$line" =~ ^--.*--$ ]]; then
        continue
    fi

    if [[ ! "$line" =~ $re ]]; then
        continue
    fi

    ts="${BASH_REMATCH[1]}"
    proc_raw="${BASH_REMATCH[5]}"
    msg="${BASH_REMATCH[6]}"
    proc="${proc_raw%%\[*}"

    if ! epoch=$(date -d "$ts" +%s 2>/dev/null); then
        continue
    fi

    printf '%s %s: %s\n' "$epoch" "$proc" "$msg"
done <<< "$output"
