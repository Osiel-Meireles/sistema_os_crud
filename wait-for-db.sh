#!/bin/bash
set -e

echo "⏳ Aguardando PostgreSQL ficar pronto..."
until pg_isready -h $DB_HOST -U $DB_USER -d postgres; do
  sleep 3
done

echo "✅ Banco de dados acessível."

# Cria o banco principal se ainda não existir
psql -h $DB_HOST -U $DB_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE \"$DB_NAME\""

echo "✅ Banco $DB_NAME garantido."

exec "$@"
