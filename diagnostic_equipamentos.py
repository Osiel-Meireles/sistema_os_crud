# diagnostic_equipamentos.py - VERSÃO PARA DOCKER

import psycopg2
from sqlalchemy import create_engine, text
import pandas as pd
import os

# IMPORTANTE: Usa as mesmas variáveis de ambiente do app.py
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'postgres-dev'),  # Nome do serviço no docker-compose
    'port': 5432,
    'database': os.getenv('DB_NAME', 'ordens_servico'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '1234')
}

print("=" * 60)
print("DIAGNÓSTICO DA TABELA EQUIPAMENTOS")
print("=" * 60)
print(f"\n🔍 Configuração de Conexão:")
print(f"   Host: {DB_CONFIG['host']}")
print(f"   Database: {DB_CONFIG['database']}")
print(f"   User: {DB_CONFIG['user']}")
print(f"   Port: {DB_CONFIG['port']}")

try:
    # Teste 1: Conexão básica com psycopg2
    print("\n[TESTE 1] Conectando ao banco com psycopg2...")
    conn_pg = psycopg2.connect(**DB_CONFIG)
    cur = conn_pg.cursor()
    print("✅ Conexão estabelecida com sucesso!")
    
    # Teste 2: Verificar se a tabela existe
    print("\n[TESTE 2] Verificando se a tabela 'equipamentos' existe...")
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'equipamentos'
        );
    """)
    table_exists = cur.fetchone()[0]
    
    if table_exists:
        print("✅ Tabela 'equipamentos' encontrada!")
    else:
        print("❌ Tabela 'equipamentos' NÃO existe no banco!")
        print("   Execute a aplicação primeiro para criar as tabelas.")
        exit()
    
    # Teste 3: Contar registros
    print("\n[TESTE 3] Contando registros na tabela...")
    cur.execute("SELECT COUNT(*) FROM equipamentos;")
    total_registros = cur.fetchone()[0]
    print(f"📊 Total de registros: {total_registros}")
    
    if total_registros == 0:
        print("\n⚠️  PROBLEMA IDENTIFICADO: A tabela está vazia!")
        print("   Verifique se a importação foi realizada corretamente.")
        print("\n💡 Para importar dados:")
        print("   1. Acesse a aplicação no navegador")
        print("   2. Vá em 'Importar Dados'")
        print("   3. Faça upload do arquivo CSV de equipamentos")
    
    # Teste 4: Verificar estrutura da tabela
    print("\n[TESTE 4] Verificando estrutura da tabela...")
    cur.execute("""
        SELECT column_name, data_type, character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = 'equipamentos'
        ORDER BY ordinal_position;
    """)
    colunas = cur.fetchall()
    print("\nColunas encontradas:")
    for col in colunas:
        col_name, col_type, col_length = col
        length_info = f"({col_length})" if col_length else ""
        print(f"  - {col_name}: {col_type}{length_info}")
    
    # Teste 5: Buscar primeiros 5 registros
    if total_registros > 0:
        print("\n[TESTE 5] Buscando os primeiros 5 registros...")
        cur.execute("""
            SELECT id, hostname, categoria, secretaria, ip 
            FROM equipamentos 
            ORDER BY id 
            LIMIT 5;
        """)
        registros = cur.fetchall()
        print("\nPrimeiros registros:")
        for reg in registros:
            print(f"  ID: {reg[0]}, Hostname: {reg[1]}, Categoria: {reg[2]}, Secretaria: {reg[3]}, IP: {reg[4]}")
        
        # Teste 6: Verificar dados nulos
        print("\n[TESTE 6] Verificando campos obrigatórios...")
        cur.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE hostname IS NULL) as hostname_null,
                COUNT(*) FILTER (WHERE categoria IS NULL) as categoria_null,
                COUNT(*) FILTER (WHERE secretaria IS NULL) as secretaria_null,
                COUNT(*) FILTER (WHERE especificacao IS NULL) as especificacao_null
            FROM equipamentos;
        """)
        nulls = cur.fetchone()
        if sum(nulls) > 0:
            print("⚠️  Registros com campos obrigatórios nulos:")
            print(f"   - Hostname: {nulls[0]}")
            print(f"   - Categoria: {nulls[1]}")
            print(f"   - Secretaria: {nulls[2]}")
            print(f"   - Especificação: {nulls[3]}")
        else:
            print("✅ Todos os registros possuem campos obrigatórios preenchidos")
    
    # Teste 7: Testar query com SQLAlchemy (igual ao app)
    if total_registros > 0:
        print("\n[TESTE 7] Testando consulta com SQLAlchemy (simulando app)...")
        engine = create_engine(
            f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        )
        
        query = text("SELECT id, hostname, categoria, secretaria, ip, mac, especificacao FROM equipamentos LIMIT 10")
        
        with engine.connect() as con:
            result = con.execute(query)
            rows = result.fetchall()
            columns = result.keys()
            df = pd.DataFrame(rows, columns=columns)
        
        if df.empty:
            print("❌ DataFrame retornou vazio com SQLAlchemy!")
        else:
            print(f"✅ SQLAlchemy retornou {len(df)} registros")
            print("\nPrimeiras linhas do DataFrame:")
            print(df.to_string(index=False, max_rows=5))
            
            # Verifica tipos de dados
            print("\nTipos de dados no DataFrame:")
            for col in df.columns:
                print(f"  - {col}: {df[col].dtype}")
    
    cur.close()
    conn_pg.close()
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO CONCLUÍDO COM SUCESSO")
    print("=" * 60)
    
    if total_registros == 0:
        print("\n⚠️  PRÓXIMOS PASSOS:")
        print("   1. Acesse a aplicação e importe dados de equipamentos")
        print("   2. Execute este diagnóstico novamente")
    else:
        print("\n✅ BANCO DE DADOS OK - Dados podem ser visualizados")

except psycopg2.OperationalError as e:
    print(f"\n❌ ERRO DE CONEXÃO: {e}")
    print("\n💡 SOLUÇÕES POSSÍVEIS:")
    print(f"   1. Verifique se o host está correto: {DB_CONFIG['host']}")
    print("   2. Verifique o docker-compose.yml para o nome correto do serviço PostgreSQL")
    print("   3. Confirme que o container PostgreSQL está rodando:")
    print("      docker compose ps")
    
except Exception as e:
    print(f"\n❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
