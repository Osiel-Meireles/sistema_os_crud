# CÓDIGO COMPLETO E CORRIGIDO PARA: sistema_os_crud-main/import_export.py

import io
import pandas as pd
from pandas import DataFrame
from typing import Optional
from database import get_connection
import xlsxwriter
import re
import streamlit as st

def _read_any_excel(file) -> DataFrame:
    name = getattr(file, "name", None)
    if name and name.lower().endswith(".ods"):
        return pd.read_excel(file, engine="odf")
    try:
        return pd.read_excel(file)
    except UnicodeDecodeError:
        return pd.read_excel(file, engine="odf")

def _to_date_str(series: pd.Series) -> pd.Series:
    s = pd.to_datetime(series, errors="coerce").dt.date.astype("string")
    return s.where(~s.isna(), None)

def _to_time_str(series: pd.Series) -> pd.Series:
    t = pd.to_datetime(series, errors="coerce").dt.time
    valid_mask = pd.notna(t)
    return t.where(valid_mask).map(lambda x: x.strftime("%H:%M:%S") if pd.notna(x) else None)

def _strip_all(df: DataFrame) -> DataFrame:
    df = df.copy()
    df = df.dropna(how="all")
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype("string").str.strip()
    return df

def _read_any_file(file) -> DataFrame:
    name = getattr(file, "name", None)
    if name and name.lower().endswith(".csv"):
        try:
            df = pd.read_csv(file, sep=None, engine='python')
            return df
        except Exception:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=';', engine='python')
                return df
            except Exception:
                file.seek(0)
                df = pd.read_csv(file, sep=',', engine='python')
                return df
    return _read_any_excel(file)

def importar_os_externa(file) -> int:
    raw = _read_any_file(file)
    if len(raw) >= 2:
        raw.columns = raw.iloc[1]
        df = raw.iloc[2:].reset_index(drop=True)
    else:
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)
    
    df = _strip_all(df)
    
    rename_map = {
        "SECRETARIA": "secretaria", "SETOR": "setor", "DESCRIÇÃO": "descricao",
        "DESCRICAO": "descricao", "DATA": "data", "HORA": "hora", "OS": "numero",
        "Nº OS": "numero", "SOLICITANTE": "solicitante", "TELEFONE": "telefone",
        "TÉCNICO": "tecnico", "TECNICO": "tecnico", "SOLICITAÇÃO": "solicitacao_cliente",
        "SOLICITAÇÃO DO CLIENTE": "solicitacao_cliente", "SOLICITACAO DO CLIENTE": "solicitacao_cliente",
        "CATEGORIA": "categoria", "NÚMERO DO PATRIMÔNIO": "patrimonio",
        "NUMERO DO PATRIMONIO": "patrimonio", "Nº_PATRIMÔNIO": "patrimonio",
        "Nº PATRIMÔNIO": "patrimonio", "EQUIPAMENTO": "equipamento",
        "SERVIÇO EXECUTADO": "servico_executado", "SERVICO EXECUTADO": "servico_executado",
        "SERVIÇO_EXECUTADO": "servico_executado", "STATUS": "status",
        "DATA FINALIZADA": "data_finalizada", "DATAFINALIZADA": "data_finalizada",
        "DATA DE RETIRADA": "data_retirada", "DATADERETIRADA": "data_retirada",
        "RETIRADA POR": "retirada_por", "RETIRADAPOR": "retirada_por"
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
    raw = _read_any_file(file)
    if len(raw) >= 2:
        raw.columns = raw.iloc[1]
        df = raw.iloc[2:].reset_index(drop=True)
    else:
        raw.columns = raw.iloc[0]
        df = raw.iloc[1:].reset_index(drop=True)
    
    df = _strip_all(df)
    
    rename_map = {
        "SECRETARIA": "secretaria", "SETOR": "setor", "DESCRIÇÃO": "descricao",
        "DESCRICAO": "descricao", "DATA": "data", "HORA": "hora", "OS": "numero",
        "Nº OS": "numero", "SOLICITANTE": "solicitante", "TELEFONE": "telefone",
        "TÉCNICO": "tecnico", "TECNICO": "tecnico", "SOLICITAÇÃO": "solicitacao_cliente",
        "SOLICITAÇÃO DO CLIENTE": "solicitacao_cliente", "SOLICITACAO DO CLIENTE": "solicitacao_cliente",
        "CATEGORIA": "categoria", "NÚMERO DO PATRIMÔNIO": "patrimonio",
        "NUMERO DO PATRIMONIO": "patrimonio", "Nº_PATRIMÔNIO": "patrimonio",
        "Nº PATRIMÔNIO": "patrimonio", "EQUIPAMENTO": "equipamento",
        "SERVIÇO EXECUTADO": "servico_executado", "SERVICO EXECUTADO": "servico_executado",
        "SERVIÇO_EXECUTADO": "servico_executado", "STATUS": "status",
        "DATA FINALIZADA": "data_finalizada", "DATAFINALIZADA": "data_finalizada",
        "DATA DE RETIRADA": "data_retirada", "DATADERETIRADA": "data_retirada",
        "RETIRADA POR": "retirada_por", "RETIRADAPOR": "retirada_por"
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
    df_export = df.copy()
    for col in ['data_finalizada', 'data_retirada']:
        if col in df_export.columns and pd.api.types.is_datetime64_any_dtype(df_export[col]):
            df_export[col] = pd.to_datetime(df_export[col], utc=True).dt.tz_convert('America/Sao_Paulo')
            df_export[col] = df_export[col].dt.tz_localize(None)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_export.to_excel(writer, sheet_name="Dados Filtrados", index=False)
    buffer.seek(0)
    return buffer.getvalue()

def _normalize_mac(mac):
    """Normaliza MAC para o formato AA:BB:CC:DD:EE:FF e trata valores inválidos."""
    if pd.isna(mac) or not isinstance(mac, str) or mac.strip() == '':
        return None
    
    mac_normalized = str(mac).replace('-', ':').replace('.', ':').upper().strip()
    
    # Lista de MACs "lixo" que devem ser tratados como NULOS
    junk_macs = ["00:00:00:00:00:00", "FF:FF:FF:FF:FF:FF"]
    if mac_normalized in junk_macs:
        return None
    
    # Regex para validar o formato MAC
    if re.match(r"^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", mac_normalized):
        return mac_normalized
    
    # Se não for um MAC válido, retorna None
    return None

def importar_equipamentos(file) -> (int, int):
    """
    Importa equipamentos a partir de um arquivo CSV.
    Insere linha por linha para tratar duplicatas graciosamente.
    Retorna (registros_importados, registros_ignorados)
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError
    
    # Lê o arquivo
    df_raw = _read_any_file(file)
    total_linhas_original = len(df_raw)
    
    st.info(f"📄 Arquivo lido: {total_linhas_original} linhas encontradas")
    
    # Remove linhas completamente vazias e limpa espaços
    df = _strip_all(df_raw)
    st.info(f"🧹 Após limpeza: {len(df)} linhas restantes")
    
    # Normaliza nomes das colunas
    df.columns = [str(c).lower().strip().replace(' ', '').replace('_', '') for c in df.columns]
    
    st.write("**Colunas detectadas no CSV:**", list(df.columns))
    
    # Mapeamento flexível de colunas
    rename_map = {
        'categoria': 'categoria',
        'patrimonio': 'patrimonio',
        'patrimônio': 'patrimonio',
        'hostname': 'hostname',
        'modelo': 'especificacao',
        'modeloespecificacao': 'especificacao',
        'especificacao': 'especificacao',
        'especificação': 'especificacao',
        'secretaria': 'secretaria',
        'setor': 'setor',
        'departamento': 'setor',
        'localizacao': 'localizacao_fisica',
        'localizacaofisica': 'localizacao_fisica',
        'localizaçãofísica': 'localizacao_fisica',
        'ip': 'ip',
        'enderecoip': 'ip',
        'endereçoip': 'ip',
        'gateway': 'gateway',
        'mac': 'mac',
        'macaddress': 'mac',
        'dns': 'dns',
        'subrede': 'subrede',
        'sub-rede': 'subrede',
        'serie': 'numero_serie',
        'numeroserie': 'numero_serie',
        'númeroserie': 'numero_serie',
        'observacoes': 'observacoes',
        'observações': 'observacoes',
        'obs': 'observacoes'
    }
    
    df = df.rename(columns=rename_map)
    
    st.write("**Colunas após mapeamento:**", list(df.columns))
    
    # Define as colunas que existem na tabela 'equipamentos'
    keep_cols = [
        "categoria", "patrimonio", "hostname", "especificacao", "secretaria",
        "setor", "localizacao_fisica", "ip", "mac", "subrede", "gateway",
        "dns", "numero_serie", "observacoes"
    ]
    
    # Adiciona colunas faltantes com None
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[keep_cols]
    
    # Mostra uma amostra dos dados
    st.write("**Primeiras 3 linhas após mapeamento:**")
    st.dataframe(df.head(3))
    
    # Normaliza MAC Address
    df['mac'] = df['mac'].apply(_normalize_mac)
    
    # Garante que 'especificacao' não seja nula (usa hostname como fallback)
    df['especificacao'] = df['especificacao'].fillna(df['hostname'])
    
    # Conta quantos registros têm campos obrigatórios preenchidos
    before_drop = len(df)
    df = df.dropna(subset=['hostname', 'categoria', 'secretaria', 'especificacao'])
    after_drop = len(df)
    
    if before_drop > after_drop:
        st.warning(f"⚠️ {before_drop - after_drop} linhas removidas por falta de campos obrigatórios")
    
    if df.empty:
        st.error("❌ Nenhum registro válido encontrado após validação!")
        return 0, total_linhas_original
    
    # Conecta ao banco
    conn = get_connection()
    
    # Inserção linha por linha com tratamento de erro
    inserted = 0
    ignored = 0
    errors = []
    
    total_to_process = len(df)
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # CORREÇÃO: usa enumerate para ter controle preciso do índice
    for counter, (idx, row) in enumerate(df.iterrows(), start=1):
        try:
            # Prepara os dados da linha
            row_data = row.to_dict()
            
            # Monta a query de inserção
            insert_query = text("""
                INSERT INTO equipamentos (
                    categoria, patrimonio, hostname, especificacao, secretaria,
                    setor, localizacao_fisica, ip, mac, subrede, gateway,
                    dns, numero_serie, observacoes
                ) VALUES (
                    :categoria, :patrimonio, :hostname, :especificacao, :secretaria,
                    :setor, :localizacao_fisica, :ip, :mac, :subrede, :gateway,
                    :dns, :numero_serie, :observacoes
                )
            """)
            
            # Executa a inserção
            with conn.connect() as con:
                with con.begin():
                    con.execute(insert_query, row_data)
            
            inserted += 1
            
        except IntegrityError as e:
            # Duplicata encontrada - registra e continua
            ignored += 1
            error_detail = str(e.orig).split('\n')[0] if hasattr(e, 'orig') else str(e)
            
            # Identifica qual campo causou a duplicata
            if 'mac_key' in error_detail.lower():
                campo_dup = f"MAC={row_data.get('mac')}"
            elif 'ip_key' in error_detail.lower():
                campo_dup = f"IP={row_data.get('ip')}"
            elif 'hostname_key' in error_detail.lower():
                campo_dup = f"Hostname={row_data.get('hostname')}"
            else:
                campo_dup = "Campo desconhecido"
            
            errors.append({
                'linha': counter,
                'hostname': row_data.get('hostname'),
                'motivo': f"Duplicado: {campo_dup}"
            })
        
        except Exception as e:
            # Erro inesperado
            ignored += 1
            errors.append({
                'linha': counter,
                'hostname': row_data.get('hostname'),
                'motivo': f"Erro: {str(e)[:50]}"
            })
        
        # Atualiza barra de progresso (CORRIGIDO)
        progress = min(counter / total_to_process, 1.0)  # Garante que nunca ultrapasse 1.0
        progress_bar.progress(progress)
        status_text.text(f"Processando: {counter}/{total_to_process} | Inseridos: {inserted} | Ignorados: {ignored}")
    
    progress_bar.empty()
    status_text.empty()
    
    # Mostra resumo
    st.success(f"✅ Importação concluída!")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de linhas", total_linhas_original)
        st.metric("Registros válidos", len(df))
    with col2:
        st.metric("✅ Inseridos", inserted, delta=f"+{inserted}")
        st.metric("⚠️ Ignorados", ignored)
    
    # Mostra detalhes dos erros se houver
    if errors and len(errors) <= 20:
        with st.expander("⚠️ Ver registros ignorados", expanded=False):
            errors_df = pd.DataFrame(errors)
            st.dataframe(errors_df, use_container_width=True)
    elif errors:
        with st.expander(f"⚠️ Ver registros ignorados ({len(errors)} total)", expanded=False):
            st.warning(f"Mostrando os primeiros 20 de {len(errors)} registros ignorados:")
            errors_df = pd.DataFrame(errors[:20])
            st.dataframe(errors_df, use_container_width=True)
    
    conn.dispose()
    
    return inserted, ignored