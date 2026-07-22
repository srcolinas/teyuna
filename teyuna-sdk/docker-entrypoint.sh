#!/bin/sh
set -eu

NUM_PLAYERS="${NUM_PLAYERS:-3}"
HOST="${TEYUNA_HOST:-http://backend:8000}"

# Fresh per-run folder so host-mounted logs are never overwritten.
LOG_ROOT="${TEYUNA_LOG_ROOT:-/var/log/teyuna}"
export TEYUNA_LOG_DIR="${LOG_ROOT}/$(date +%Y-%m-%d-%H-%M)"
mkdir -p "$TEYUNA_LOG_DIR"
echo "Writing player logs to $TEYUNA_LOG_DIR"

case "$NUM_PLAYERS" in
  3)
    set -- builder:builder sleepy:sleepy skipper:skipper
    ;;
  4)
    set -- builder:builder sleepy:sleepy skipper:skipper builder:builder-1
    ;;
  *)
    echo "NUM_PLAYERS must be 3 or 4, got: $NUM_PLAYERS" >&2
    exit 1
    ;;
esac

exec teyuna-simulate --host "$HOST" "$@"
