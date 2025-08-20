# import_export.py
# -----------------------------------------------------------
# Importação/Exportação de OS Internas e Externas (PostgreSQL)
# Compatível com XLSX e ODS. Mapeia colunas das planilhas
# enviadas, normaliza datas/horas e evita duplicados simples.
# -----------------------------------------------------------

from __future__ import annotations
import io
import pandas as pd
from pandas import DataFrame
from typing import Optional
from database import get_connection
import xlsxwriter


# ========== Utilidades ==========
def _read_any_excel(file) -> DataFrame:
    """
    Lê XLSX/ODS. Se o arquivo vier do Streamlit (UploadedFile), ele tem .name.
    """
    name = getattr(file, "name", None)
    if name and name.lower().endswith(".ods"):
        return pd.read_excel(file, engine="odf")
    
    # Adicionando um fallback para o motor e codificação
    try:
        return pd.read_excel(file)
    except UnicodeDecodeError:
        # Tenta novamente com uma codificação diferente, como latin-1
        # Isso pode não funcionar com todos os motores de excel, mas é uma tentativa
        return pd.read_excel(file, engine="odf") # Se o erro persistir, o problema pode estar no arquivo .xlsx
    

def _to_date_str(series: pd.Series) -> pd.Series:
    """
    Converte datas variadas para 'YYYY-MM-DD' (string). Mantém vazio se inválido.
    """
    s = pd.to_datetime(series, errors="coerce").dt.date.astype("string")
    return s.where(~s.isna(), None)


def _to_time_str(series: pd.Series) -> pd.Series:
    """
    Converte horas variadas para 'HH:MM:SS' (string). Mantém vazio se inválido.
    """
    t = pd.to_datetime(series, errors="coerce").dt.time
    # dt.time vira dtype object; formata para HH:MM:SS
    return t.map(lambda x: x.strftime("%H:%M:%S") if pd.notna(x) else None)


def _strip_all(df: DataFrame) -> DataFrame:
    """
    Tira espaços/linhas totalmente vazias e converte tudo que é string para strip().
    """
    df = df.copy()
    # Remover linhas totalmente vazias
    df = df.dropna(how="all")
    # Strip em colunas string
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
            df[col] = df[col].astype("string").str.strip()
    return df


# ========== Importação: OS Externa ==========
def importar_os_externa(file) -> int:
    """
    Importa OS Externas a partir da planilha no formato enviado.
    - A planilha tem 2 primeiras linhas de 'cabeçalho', sendo a linha 1 os nomes reais.
    - Faz o mapeamento de colunas e insere em os_externa.
    - Evita duplicação simples baseada no número da OS (se existir no banco).
    Retorna a quantidade inserida.
    """
    raw = _read_any_excel(file)

    # Caso típico visto no arquivo: colunas "A", "Unnamed: 1", ...
    # A linha 1 contém: SECRETARIA, SETOR, DESCRIÇÃO, DATA, HORA, OS, SOLICITANTE, TELEFONE, TÉCNICO
    # Usamos a linha 1 como cabeçalho e descartamos as duas primeiras linhas.
    if len(raw) >= 2:
        raw.columns = raw.iloc[1]
        df = raw.iloc[2:].reset_index(drop=True)
    else:
        # fallback: considerar a primeira linha como cabeçalho
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)

    df = _strip_all(df)

    # Renomear colunas para o schema do banco
    rename_map = {
        "SECRETARIA": "secretaria",
        "SETOR": "setor",
        "DESCRIÇÃO": "descricao",
        "DESCRICAO": "descricao",
        "DATA": "data",
        "HORA": "hora",
        "OS": "numero",
        "Nº OS": "numero",
        "SOLICITANTE": "solicitante",
        "TELEFONE": "telefone",
        "TÉCNICO": "tecnico",
        "TECNICO": "tecnico",
    }
    # Padroniza possíveis variações de uppercase/acentos
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns=rename_map)

    # Manter somente colunas do banco
    keep_cols = ["secretaria", "setor", "descricao", "data", "hora",
                 "numero", "solicitante", "telefone", "tecnico"]
    # Algumas podem não existir; seleciona as existentes e adiciona as faltantes como None
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    df = df[keep_cols]

    # Normalizações
    df["data"] = _to_date_str(df["data"])
    df["hora"] = _to_time_str(df["hora"])

    # Evitar duplicados: usa 'numero' (se existir)
    conn = get_connection()
    try:
        existing = pd.read_sql("SELECT numero FROM os_externa WHERE numero IS NOT NULL", conn)
        existing_set = set(existing["numero"].dropna().astype(str))
    except Exception:
        existing_set = set()

    # Se 'numero' vier vazio, mantém (não dá para deduplicar de forma segura)
    if "numero" in df.columns:
        df["numero"] = df["numero"].astype("string")
        mask_new = ~df["numero"].isin(existing_set) | df["numero"].isna()
        df = df.loc[mask_new]

    # Remove linhas totalmente vazias pós-mapeamento
    df = df.dropna(how="all", subset=keep_cols)

    # Inserção no banco
    inserted = 0
    if not df.empty:
        df.to_sql("os_externa", conn, if_exists="append", index=False)
        inserted = len(df)
    
    conn.dispose()
    return inserted


# ========== Importação: OS Interna ==========
def importar_os_interna(file) -> int:
    """
    Importa OS Internas a partir da planilha no formato enviado (.ods).
    - A primeira linha (índice 0) contém os nomes das colunas.
    - Faz o mapeamento de colunas e insere em os_interna.
    - Evita duplicação simples baseada no número (O.S).
    Retorna a quantidade inserida.
    """
    raw = _read_any_excel(file)

    # Padrão visto: linha 0 contém o cabeçalho com "O.S, SECRETARIA, UNIDADE, DATA DEENTRADA, ..."
    # Às vezes o pandas cria colunas "Unnamed: X"; então forçamos linha 0 como cabeçalho.
    if len(raw) >= 1:
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)
    else:
        df = raw.copy()

    df = _strip_all(df)

    # Normaliza nomes de colunas (uppercase) para mapeamento robusto
    df.columns = [str(c).strip().upper() for c in df.columns]

    # Mapeamento com variações observadas (sem espaços ou com erros de OCR)
    rename_map = {
        "O.S": "numero",
        "OS": "numero",
        "SECRETARIA": "secretaria",
        "DATA DE ENTRADA": "data",
        "DATA DEENTRADA": "data",
        "DATADEENTRADA": "data",
        "DATA ENTRADA": "data",
        "DATA FINALIZADA": "data_finalizada",
        "DATAFINALIZADA": "data_finalizada",
        "DATA DE RETIRADA": "data_retirada",
        "DATA DERETIRADA": "data_retirada",
        "DATADE RETIRADA": "data_retirada",
        "NOME DO SOLICITANTE": "solicitante",
        "NOME DOSOLICITANTE": "solicitante",
        "RETIRADA POR": "retirada_por",
        "RETIRADAPOR": "retirada_por",
        "EQUIPAMENTO": "equipamento",
        "DESCRIÇÃO": "descricao",
        "DESCRICAO": "descricao",
        "STATUS": "status",
        # "UNIDADE": "unidade",  # <-- Removido, pois a coluna não existe no banco de dados
        # "OBS": "obs",          # <-- Removido, pois a coluna não existe no banco de dados
    }
    df = df.rename(columns=rename_map)

    keep_cols = [
        "numero", "secretaria", 
        "data", "data_finalizada", "data_retirada", "solicitante",
        "retirada_por", "equipamento", "descricao", "status"
    ]
    
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    df = df[keep_cols]

    # Normalizações de data
    for col in ["data", "data_finalizada", "data_retirada"]:
        df[col] = _to_date_str(df[col])

    # Evitar duplicados por 'numero' (O.S)
    conn = get_connection()
    try:
        existing = pd.read_sql("SELECT numero FROM os_interna WHERE numero IS NOT NULL", conn)
        existing_set = set(existing["numero"].dropna().astype(str))
    except Exception:
        existing_set = set()

    df["numero"] = df["numero"].astype("string")
    mask_new = ~df["numero"].isin(existing_set) | df["numero"].isna()
    df = df.loc[mask_new]

    # Remove linhas totalmente vazias pós-mapeamento
    df = df.dropna(how="all", subset=keep_cols)

    inserted = 0
    if not df.empty:
        df.to_sql("os_interna", conn, if_exists="append", index=False)
        inserted = len(df)
    
    conn.dispose()
    return inserted


# ========== Exportação: Excel único ==========
def exportar_para_excel(path_arquivo: Optional[str] = "auditoria.xlsx") -> bytes | str:
    """
    Exporta todas as OS (interna e externa) para um único Excel com 2 abas.
    - Se path_arquivo for fornecido, salva no disco e retorna o caminho (str).
    - Caso contrário, retorna os bytes para usar em st.download_button.
    """
    conn = get_connection()
    
    # Colunas padronizadas para ambas as tabelas
    standard_cols = [
        "numero", "secretaria", "setor", "data", "hora", "solicitante",
        "telefone", "equipamento", "descricao", "status",
        "data_finalizada", "data_retirada", "retirada_por", "tecnico", "tipo"
    ]
    
    df_interna_query = """
        SELECT
            numero, secretaria, setor, data, hora, solicitante,
            telefone, equipamento, descricao, status,
            data_finalizada, data_retirada, retirada_por, tecnico, 'Interna' as tipo
        FROM os_interna
    """
    df_interna = pd.read_sql(df_interna_query, conn)

    df_externa_query = """
        SELECT
            numero, secretaria, setor, data, hora, solicitante,
            telefone, equipamento, descricao, status,
            data_finalizada, data_retirada, retirada_por, tecnico, 'Externa' as tipo
        FROM os_externa
    """
    df_externa = pd.read_sql(df_externa_query, conn)
    
    # A conexão SQLAlchemy deve ser fechada com `dispose()`
    conn.dispose()

    if path_arquivo:
        with pd.ExcelWriter(path_arquivo) as writer:
            df_interna[standard_cols].to_excel(writer, sheet_name="OS Interna", index=False)
            df_externa[standard_cols].to_excel(writer, sheet_name="OS Externa", index=False)
        return path_arquivo

    # Retorna bytes para download em Streamlit
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_interna[standard_cols].to_excel(writer, sheet_name="OS Interna", index=False)
        df_externa[standard_cols].to_excel(writer, sheet_name="OS Externa", index=False)
    buffer.seek(0)
    return buffer.getvalue()


def exportar_filtrados_para_excel(df: pd.DataFrame) -> bytes:
    """
    Exporta um DataFrame filtrado para um único arquivo Excel em memória.
    Retorna os bytes para usar em st.download_button.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Dados Filtrados", index=False)
    buffer.seek(0)
    return buffer.getvalue()