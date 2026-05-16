#!/bin/sh
set -e

# --- Railway PostgreSQL ---
export LISTMONK_db__host="${PGHOST}"
export LISTMONK_db__port="${PGPORT:-5432}"
export LISTMONK_db__user="${PGUSER}"
export LISTMONK_db__password="${PGPASSWORD}"
export LISTMONK_db__database="${PGDATABASE}"

# --- App ---
export LISTMONK_app__address="0.0.0.0:${PORT:-9000}"

echo "==> Running DB install/upgrade..."
./listmonk --install --yes --config config.toml || \
./listmonk --upgrade --yes --config config.toml

echo "==> Starting Listmonk..."
exec ./listmonk --config config.toml
