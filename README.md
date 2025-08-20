## Sistema de Registro de Ordens de Serviço (OS)

Este é um sistema web desenvolvido em Python com o framework [Streamlit](https://streamlit.io/) para a gestão de ordens de serviço. O projeto foi arquitetado para ser robusto e fácil de implantar, utilizando um banco de dados PostgreSQL e conteinerização com Docker.

### Visão Geral

O objetivo do sistema é simplificar o registro, acompanhamento e a finalização de ordens de serviço, dividindo-as em dois tipos principais: Internas e Externas. A aplicação oferece uma interface intuitiva para o gerenciamento diário e inclui funcionalidades avançadas de importação e exportação de dados, bem como ferramentas de filtragem e busca.

### Tecnologias

  * **Backend:** Python
  * **Framework Web:** Streamlit
  * **Banco de Dados:** PostgreSQL
  * **Gerenciamento de Dependências:** `pip`
  * **Conteinerização:** Docker e Docker Compose
  * **Manipulação de Dados:** Pandas, SQLAlchemy

### Funcionalidades

O sistema foi projetado para atender às principais necessidades de um fluxo de trabalho de ordens de serviço, com as seguintes funcionalidades destacadas:

  * **Registro de OS:** Crie novas ordens de serviço (Internas e Externas) através de formulários dedicados, preenchendo informações como número da OS, secretaria, solicitante, descrição do problema, e técnico responsável.
  * **Visualização de Dados:** Visualize as OS cadastradas diretamente em tabelas interativas na interface da aplicação.
  * **Filtro:** Encontre rapidamente informações sobre as OS utilizando filtros por tipo, secretaria, e período de tempo (data de início e fim).
  * **Baixa em OS:** Finalize uma OS de maneira simples, registrando a data de conclusão, o serviço executado e quem realizou a retirada do equipamento.
  * **Importação de Dados:** Importe dados de ordens de serviço de planilhas Excel (`.xlsx`) ou ODS (`.ods`). O sistema normaliza os dados automaticamente e evita a duplicação de registros baseados no número da OS.
  * **Exportação de Dados:** Exporte os dados completos de todas as OS (Internas e Externas) para um único arquivo Excel, com abas separadas para cada tipo.

### Configuração e Execução

Para iniciar o projeto, siga os passos abaixo. A maneira mais recomendada é usando Docker Compose para gerenciar o ambiente de forma automática.

#### Pré-requisitos

Certifique-se de que você tem o [Docker](https://docs.docker.com/get-docker/) e o [Docker Compose](https://docs.docker.com/compose/install/) instalados em seu sistema.

#### Passos

1.  **Clone o Repositório**

    Se você ainda não tem o código-fonte, obtenha-o.

2.  **Configurar o Banco de Dados e Rodar a Aplicação**

    O arquivo `docker-compose.yml` já está configurado para iniciar o banco de dados PostgreSQL e a aplicação Streamlit.

    ```yaml
    version: '3.8'

    services:
      app:
        build: .
        ports:
          - "8501:8501"
        environment:
          - DB_HOST=db
          - DB_NAME=ordens_servico
          - DB_USER=postgres
          - DB_PASSWORD=1234
        depends_on:
          - db

      db:
        image: postgres:13
        restart: always
        environment:
          - POSTGRES_DB=ordens_servico
          - POSTGRES_USER=postgres
          - POSTGRES_PASSWORD=1234
        volumes:
          - postgres_data:/var/lib/postgresql/data/
        ports:
          - "5432:5432"

    volumes:
      postgres_data:
    ```

    Os arquivos de configuração e o script `setup.py` se encarregam de criar a base de dados (`ordens_servico`), o usuário e as tabelas necessárias automaticamente. Caso você tenha um banco de dados SQLite antigo (`ordens_servico.db`), o script `migrate_data.py` será executado para migrar os dados para o novo banco PostgreSQL.

3.  **Iniciar o Ambiente**

    A partir da pasta raiz do projeto, execute o seguinte comando:

    ```bash
    docker-compose up --build
    ```

    Isso irá construir a imagem da aplicação, baixar a imagem do PostgreSQL e iniciar ambos os contêineres. O script de inicialização (`setup.py`) será executado automaticamente.

4.  **Acessar a Aplicação**

    Após a inicialização, a aplicação estará disponível em seu navegador no endereço:

    `http://localhost:8501`

A aplicação está pronta para ser utilizada. O logo da prefeitura será exibido no topo da página.
