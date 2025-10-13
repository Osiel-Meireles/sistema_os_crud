#!/bin/bash

set -e

echo "⏳ Aguardando PostgreSQL ficar pronto..."

export PGPASSWORD=$DB_PASSWORD

# Aguardar o servidor PostgreSQL iniciar
until pg_isready -h $DB_HOST -U $DB_USER -d postgres; do
  echo "⏳ Aguardando servidor PostgreSQL..."
  sleep 3
done

echo "✅ Servidor PostgreSQL acessível."

# Aguardar o banco específico estar disponível OU criá-lo
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
  # Tentar conectar ao banco específico
  if psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1" > /dev/null 2>&1; then
    echo "✅ Banco $DB_NAME já existe e está acessível."
    break
  fi
  
  # Se não existir, tentar criar
  echo "🔧 Tentando criar banco $DB_NAME..."
  psql -h $DB_HOST -U $DB_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
  psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE \"$DB_NAME\""
  
  attempt=$((attempt + 1))
  sleep 2
done

if [ $attempt -eq $max_attempts ]; then
  echo "❌ Falha ao garantir banco $DB_NAME após $max_attempts tentativas"
  exit 1
fi

echo "✅ Banco $DB_NAME garantido e acessível."

unset PGPASSWORD

exec "$@"
