FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y postgresql-client cron

# Cria o diretório da aplicação
WORKDIR /app

# Copia o script de backup e o arquivo do cron para dentro da imagem
COPY backup.sh .
COPY crontab.txt /etc/cron.d/backup-cron

# Dá permissão de execução para o script de backup
RUN chmod +x /app/backup.sh

# Dá as permissões corretas para o arquivo do cron
RUN chmod 0644 /etc/cron.d/backup-cron
RUN crontab /etc/cron.d/backup-cron

# Cria um arquivo de log para o cron
RUN touch /var/log/cron.log

# Comando para iniciar o serviço do cron em primeiro plano e mostrar os logs
CMD cron && tail -f /var/log/cron.log
