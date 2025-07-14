import streamlit as st
import pandas as pd
import altair as alt
import io

@st.cache_data
def load_csv(data, sep, enc, na_values):
    try:
        df = pd.read_csv(
            io.BytesIO(data),
            sep=sep,
            encoding=enc,
            na_values=na_values,
            parse_dates=True,
            dayfirst=True,
            infer_datetime_format=True,
            low_memory=False
        )
        return df, None
    except Exception as e:
        return None, str(e)

def trova_colonna_costo(df):
    # Cerca la colonna che contiene sia 'costo' che 'stimato'
    for col in df.columns:
        nome = col.lower().replace(" ", "")
        if "costo" in nome and "stimato" in nome:
            return col
    return None

def main():
    st.set_page_config(page_title="Dashboard Viaggi e Compensi", layout="wide")
    st.title("Dashboard Viaggi e Compensi per Autista")

    # Sidebar: CSV options + filters + pagination
    st.sidebar.header("Caricamento e Filtri")
    uploaded = st.sidebar.file_uploader("File CSV", type="csv")
    sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
    enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
    na_list = [v.strip() for v in st.sidebar.text_input("Valori NaN (sep. virgola)", "").split(",") if v.strip()]

    if not uploaded:
        st.info("Carica un file CSV per iniziare")
        return

    df, error = load_csv(uploaded.read(), sep, enc, na_list)
    if error:
        st.error(f"Errore lettura CSV: {error}")
        return

    # Preprocessing
    if 'Sequenza delle strutture' in df.columns:
        seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
        df['Origine'], df['Destinazione'] = seq[0], seq[1]
    if 'ID Veicolo' in df.columns:
        df

