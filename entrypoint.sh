#!/bin/bash
set -e

# Escreve as variáveis de ambiente em um arquivo que o cron possa ler
printenv | grep -E "DB_HOST|DB_NAME|DB_USER|DB_PASSWORD|TZ" > /etc/environment

echo "✅ Variáveis de ambiente configuradas para o cron."

# Inicia o serviço do cron e exibe os logs
cron && tail -f /var/log/cron.log
