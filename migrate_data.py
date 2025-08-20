import pandas as pd
import sqlite3
from sqlalchemy import create_engine

sqlite_conn = sqlite3.connect("ordens_servico.db", detect_types=sqlite3.PARSE_DECLTYPES)
sqlite_conn.text_factory = lambda b: b.decode("latin-1", errors="ignore")


DB_HOST = "localhost"
DB_NAME = "ordens_servico"
DB_USER = "postgres"
DB_PASSWORD = "root"

try:
    engine_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    pg_conn = create_engine(engine_url)

    df_interna = pd.read_sql_query("SELECT * FROM os_interna", sqlite_conn)
    df_interna.to_sql("os_interna", pg_conn, if_exists="append", index=False)
    print("Dados de os_interna migrados com sucesso.")

    df_externa = pd.read_sql_query("SELECT * FROM os_externa", sqlite_conn)
    df_externa.to_sql("os_externa", pg_conn, if_exists="append", index=False)
    print("Dados de os_externa migrados com sucesso.")

except Exception as e:
    print(f"Ocorreu um erro durante a migração: {e}")
finally:
    sqlite_conn.close()
    if 'pg_conn' in locals():
        pg_conn.dispose()