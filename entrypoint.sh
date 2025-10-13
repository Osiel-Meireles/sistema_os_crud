#!/bin/bash
set -e

# Cria um arquivo que exporta as variáveis de ambiente
echo "export DB_HOST=${DB_HOST}" > /app/.env.sh
echo "export DB_NAME=${DB_NAME}" >> /app/.env.sh
echo "export DB_USER=${DB_USER}" >> /app/.env.sh
echo "export DB_PASSWORD=${DB_PASSWORD}" >> /app/.env.sh
echo "export TZ=${TZ}" >> /app/.env.sh

echo "✅ Variáveis de ambiente salvas em /app/.env.sh"

# Inicia o serviço do cron e exibe os logs
cron && tail -f /var/log/cron.log
