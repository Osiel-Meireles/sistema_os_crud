import io
import pandas as pd
from pandas import DataFrame
from typing import Optional
from database import get_connection
import xlsxwriter


def _read_any_excel(file) -> DataFrame:
    """
    Lê XLSX/ODS. Se o arquivo vier do Streamlit (UploadedFile), ele tem .name.
    """
    name = getattr(file, "name", None)
    if name and name.lower().endswith(".ods"):
        return pd.read_excel(file, engine="odf")
    
    try:
        return pd.read_excel(file)
    except UnicodeDecodeError:
        return pd.read_excel(file, engine="odf")
    

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
    valid_mask = pd.notna(t)
    return t.where(valid_mask).map(lambda x: x.strftime("%H:%M:%S") if pd.notna(x) else None)


def _strip_all(df: DataFrame) -> DataFrame:
    """
    Tira espaços/linhas totalmente vazias e converte tudo que é string para strip().
    """
    df = df.copy()
    df = df.dropna(how="all")
    
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype("string").str.strip()
    return df


def _read_any_file(file) -> DataFrame:
    """
    Lê XLSX, ODS e CSV. Detecta o delimitador do CSV.
    """
    name = getattr(file, "name", None)
    if name and name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(file, sep=None, engine='python')
            return df
        except:
            file.seek(0)
            df = pd.read_csv(file, sep=';', engine='python')
            return df
    return _read_any_excel(file)


def importar_os_externa(file) -> int:
    """
    Importa OS Externas a partir da planilha no formato de OS Externa.
    - A planilha tem 2 primeiras linhas de 'cabeçalho', sendo a linha 1 os nomes reais.
    - Faz o mapeamento de colunas e insere em os_externa.
    - Evita duplicação simples baseada no número da OS (se existir no banco).
    Retorna a quantidade inserida.
    """
    raw = _read_any_file(file)

    if len(raw) >= 2:
        raw.columns = raw.iloc[1]
        df = raw.iloc[2:].reset_index(drop=True)
    else:
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)

    df = _strip_all(df)

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
        "SOLICITAÇÃO": "solicitacao_cliente",
        "SOLICITAÇÃO DO CLIENTE": "solicitacao_cliente",
        "SOLICITACAO DO CLIENTE": "solicitacao_cliente",
        "CATEGORIA": "categoria",
        "NÚMERO DO PATRIMÔNIO": "patrimonio",
        "NUMERO DO PATRIMONIO": "patrimonio",
        "Nº_PATRIMÔNIO": "patrimonio",
        "Nº PATRIMÔNIO": "patrimonio",
        "EQUIPAMENTO": "equipamento",
        "SERVIÇO EXECUTADO": "servico_executado",
        "SERVICO EXECUTADO": "servico_executado",
        "SERVIÇO_EXECUTADO": "servico_executado",
        "STATUS": "status",
        "DATA FINALIZADA": "data_finalizada",
        "DATAFINALIZADA": "data_finalizada",
        "DATA DE RETIRADA": "data_retirada",
        "DATADERETIRADA": "data_retirada",
        "RETIRADA POR": "retirada_por",
        "RETIRADAPOR": "retirada_por"
    }
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns=rename_map)

    keep_cols = ["secretaria", "setor", "descricao", "data", "hora",
                 "numero", "solicitante", "telefone", "tecnico",
                 "solicitacao_cliente", "categoria", "patrimonio", "equipamento",
                 "servico_executado", "status", "data_finalizada",
                 "data_retirada", "retirada_por"]
    
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    df = df[keep_cols]

    df["data"] = _to_date_str(df["data"])
    df["hora"] = _to_time_str(df["hora"])

    conn = get_connection()
    try:
        existing = pd.read_sql("SELECT numero FROM os_externa WHERE numero IS NOT NULL", conn)
        existing_set = set(existing["numero"].dropna().astype(str))
    except Exception:
        existing_set = set()

    if "numero" in df.columns:
        df["numero"] = df["numero"].astype("string")
        mask_new = ~df["numero"].isin(existing_set) | df["numero"].isna()
        df = df.loc[mask_new]

    df = df.dropna(how="all", subset=["numero"])

    inserted = 0
    if not df.empty:
        df.to_sql("os_externa", conn, if_exists="append", index=False)
        inserted = len(df)
    
    conn.dispose()
    return inserted


def importar_os_interna(file) -> int:
    """
    Importa OS Internas a partir da planilha no formato de OS Externa.
    - A planilha tem 2 primeiras linhas de 'cabeçalho', sendo a linha 1 os nomes reais.
    - Faz o mapeamento de colunas e insere em os_interna.
    - Evita duplicação simples baseada no número da OS (se existir no banco).
    Retorna a quantidade inserida.
    """
    raw = _read_any_file(file)

    if len(raw) >= 2:
        raw.columns = raw.iloc[1]
        df = raw.iloc[2:].reset_index(drop=True)
    else:
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)

    df = _strip_all(df)

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
        "SOLICITAÇÃO": "solicitacao_cliente",
        "SOLICITAÇÃO DO CLIENTE": "solicitacao_cliente",
        "SOLICITACAO DO CLIENTE": "solicitacao_cliente",
        "CATEGORIA": "categoria",
        "NÚMERO DO PATRIMÔNIO": "patrimonio",
        "NUMERO DO PATRIMONIO": "patrimonio",
        "Nº_PATRIMÔNIO": "patrimonio",
        "Nº PATRIMÔNIO": "patrimonio",
        "EQUIPAMENTO": "equipamento",
        "SERVIÇO EXECUTADO": "servico_executado",
        "SERVICO EXECUTADO": "servico_executado",
        "SERVIÇO_EXECUTADO": "servico_executado",
        "STATUS": "status",
        "DATA FINALIZADA": "data_finalizada",
        "DATAFINALIZADA": "data_finalizada",
        "DATA DE RETIRada": "data_retirada",
        "DATADERETIRADA": "data_retirada",
        "RETIRADA POR": "retirada_por",
        "RETIRADAPOR": "retirada_por"
    }
    df.columns = [str(c).strip().upper() for c in df.columns]
    df = df.rename(columns=rename_map)

    keep_cols = ["secretaria", "setor", "descricao", "data", "hora",
                 "numero", "solicitante", "telefone", "tecnico",
                 "solicitacao_cliente", "categoria", "patrimonio", "equipamento",
                 "servico_executado", "status", "data_finalizada",
                 "data_retirada", "retirada_por"]
    
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    df = df[keep_cols]

    df["data"] = _to_date_str(df["data"])
    df["hora"] = _to_time_str(df["hora"])
    
    conn = get_connection()
    try:
        existing = pd.read_sql("SELECT numero FROM os_interna WHERE numero IS NOT NULL", conn)
        existing_set = set(existing["numero"].dropna().astype(str))
    except Exception:
        existing_set = set()

    if "numero" in df.columns:
        df["numero"] = df["numero"].astype("string")
        mask_new = ~df["numero"].isin(existing_set) | df["numero"].isna()
        df = df.loc[mask_new]

    df = df.dropna(how="all", subset=["numero"])

    inserted = 0
    if not df.empty:
        df.to_sql("os_interna", conn, if_exists="append", index=False)
        inserted = len(df)
    
    conn.dispose()
    return inserted


def exportar_para_excel(path_arquivo: Optional[str] = "auditoria.xlsx") -> bytes | str:
    """
    Exporta todas as OS (interna e externa) para um único Excel com 2 abas.
    - Se path_arquivo for fornecido, salva no disco e retorna o caminho (str).
    - Caso contrário, retorna os bytes para usar em st.download_button.
    """
    conn = get_connection()
    
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
    
    conn.dispose()

    if path_arquivo:
        with pd.ExcelWriter(path_arquivo) as writer:
            df_interna[standard_cols].to_excel(writer, sheet_name="OS Interna", index=False)
            df_externa[standard_cols].to_excel(writer, sheet_name="OS Externa", index=False)
        return path_arquivo

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
    df_export = df.copy()

    # --- INÍCIO DA CORREÇÃO ---
    # Converte colunas de data com fuso horário para 'timezone-naive' antes de exportar
    for col in ['data_finalizada', 'data_retirada']:
        if col in df_export.columns and pd.api.types.is_datetime64_any_dtype(df_export[col]):
            # Converte para o fuso horário de São Paulo e depois remove a informação de timezone
            df_export[col] = pd.to_datetime(df_export[col], utc=True).dt.tz_convert('America/Sao_Paulo')
            df_export[col] = df_export[col].dt.tz_localize(None)
    # --- FIM DA CORREÇÃO ---

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, sheet_name="Dados Filtrados", index=False)
    buffer.seek(0)
    return buffer.getvalue()
