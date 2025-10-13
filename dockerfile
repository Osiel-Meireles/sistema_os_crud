FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y postgresql-client cron

# Cria o diretório da aplicação
WORKDIR /app

# Copia o novo entrypoint, o script de backup e o arquivo do cron
COPY entrypoint.sh .
COPY backup.sh .
COPY crontab.txt /etc/cron.d/backup-cron

# Dá as permissões corretas para os arquivos
RUN chmod +x /app/entrypoint.sh
RUN chmod +x /app/backup.sh
RUN chmod 0644 /etc/cron.d/backup-cron
RUN crontab /etc/cron.d/backup-cron

# Cria um arquivo de log para o cron
RUN touch /var/log/cron.log

# Define o entrypoint como o comando principal do contêiner
ENTRYPOINT ["/app/entrypoint.sh"]
