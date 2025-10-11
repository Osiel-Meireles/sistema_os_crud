#!/bin/bash
set -e

echo "⏳ Aguardando PostgreSQL ficar pronto..."
# Exporta a senha para que o pg_isready e psql possam usá-la
export PGPASSWORD=$DB_PASSWORD

# O loop agora usa as variáveis de ambiente corretas
until pg_isready -h $DB_HOST -U $DB_USER -d postgres; do
  sleep 3
done

echo "✅ Banco de dados acessível."

# Cria o banco principal se ainda não existir
psql -h $DB_HOST -U $DB_USER -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    psql -h $DB_HOST -U $DB_USER -d postgres -c "CREATE DATABASE \"$DB_NAME\""

echo "✅ Banco $DB_NAME garantido."

# Limpa a senha da variável de ambiente por segurança
unset PGPASSWORD

exec "$@"
