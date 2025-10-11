FROM python:3.10-slim

# Instala o cliente do PostgreSQL
RUN apt-get update && apt-get install -y postgresql-client

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

# Dá permissão de execução para o script de espera
RUN chmod +x ./wait-for-db.sh

# Comando corrigido: inicia a aplicação diretamente
CMD ["./wait-for-db.sh", "streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]
