
#!/bin/bash

# Define as variáveis de conexão com o banco de dados
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_NAME=${DB_NAME}

# Define o diretório de backup dentro do contêiner
BACKUP_DIR="/backups"
# Define o formato do nome do arquivo de backup com data e hora
DATE_FORMAT=$(date "+%Y-%m-%d_%H-%M-%S")
BACKUP_FILE="${BACKUP_DIR}/backup_${DATE_FORMAT}.sql.gz"

# Mensagem de log
echo "Iniciando backup do banco de dados '${DB_NAME}' em ${BACKUP_FILE}..."

# Exporta a senha para que o pg_dump possa usá-la sem prompt interativo
export PGPASSWORD=$DB_PASSWORD

# Executa o pg_dump, comprime a saída com gzip e salva no arquivo
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME | gzip > $BACKUP_FILE

# Limpa a senha da variável de ambiente
unset PGPASSWORD

# Verifica se o backup foi criado com sucesso
if [ $? -eq 0 ]; then
  echo "Backup concluído com sucesso."
else
  echo "ERRO: Falha ao criar o backup." >&2
  exit 1
fi

# Limpeza: Remove backups mais antigos que 7 dias
echo "Limpando backups antigos (mais de 7 dias)..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -exec rm {} \;
echo "Limpeza concluída."
echo "-------------------------------------------"
