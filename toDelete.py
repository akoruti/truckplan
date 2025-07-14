# app_rejected.py

import streamlit as st
import pandas as pd
import altair as alt
import io

# Configurazione pagina
st.set_page_config(page_title="Dashboard Viaggi e Compensi", layout="wide")
st.title("Dashboard Viaggi e Compensi per Autista")

# 1. Upload del file
uploaded_file = st.file_uploader("Carica il file CSV dei viaggi", type="csv")
if not uploaded_file:
    st.info("Carica un CSV per analizzare i viaggi e i compensi.")
    st.stop()

# 2. Opzioni di lettura CSV
st.sidebar.subheader("Opzioni Lettura CSV")
delimiter = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
encoding = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
na_values = st.sidebar.text_input("Valori da trattare come NaN (separati da virgola)", value="")
na_list = [v.strip() for v in na_values.split(",") if v.strip()]
preview_lines = st.sidebar.number_input("Righe anteprima", min_value=5, max_value=100, value=5)

# 3. Lettura CSV con caching e gestione errori
@st.cache_data
def load_csv(data, delim, enc, nas):
    try:
        df = pd.read_csv(
            io.BytesIO(data),
            sep=delim,
            encoding=enc,
            na_values=nas,
            parse_dates=True,
            dayfirst=True,
            infer_datetime_format=True,
            low_memory=False
        )
        return df, None
    except Exception as e:
        return None, str(e)

raw = uploaded_file.read()
df, error = load_csv(raw, delimiter, encoding, na_list)
if error:
    st.error(f"Errore lettura CSV: {error}")
    st.stop()

# 4. Anteprima dati
st.subheader("Anteprima Dati")
st.write(df.head(preview_lines))

# 5. Parsing colonne utili
if 'Sequenza delle strutture' in df.columns:
    seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
    df['Origine'], df['Destinazione'] = seq[0], seq[1]
if 'ID Veicolo' in df.columns:
    df['Targa'] = df['ID Veicolo'].astype(str).str.extract(r'OTHR-(.*)')

# 6. Estrazione compensi e collegamento ad autisti
# Assicuriamo che 'Conducente' e 'Costo stimato' esistano e siano convertiti
if 'Costo stimato' in df.columns:
    df['Costo_Num'] = pd.to_numeric(df['Costo stimato'], errors='coerce')
else:
    df['Costo_Num'] = pd.NA

# 7. Filtri principali
st.sidebar.subheader("Filtri")
stato_options = df['Stato'].unique().tolist() if 'Stato' in df.columns else []
selected_states = st.sidebar.multiselect("Stato viaggi", stato_options, default=stato_options)
carriers = df['Corriere'].unique().tolist() if 'Corriere' in df.columns else []
selected_carriers = st.sidebar.multiselect("Corriere", carriers, default=carriers)
filtered_df = df[df['Stato'].isin(selected_states) & df['Corriere'].isin(selected_carriers)]

# 8. Overview viaggi
st.subheader("Overview Stati Viaggi")
state_counts = filtered_df['Stato'].value_counts().reset_index()
state_counts.columns = ['Stato', 'Conteggio']
st.dataframe(state_counts)

# 9. Analisi compensi per autista
if 'Conducente' in df.columns:
    st.subheader("Compenso Totale e Medio per Autista")
    stats = (
        filtered_df.groupby('Conducente')['Costo_Num']
        .agg(Totale='sum', Media='mean', Viaggi='count')
        .reset_index()
        .sort_values('Totale', ascending=False)
    )
    # Selettore top N
    top_n = st.sidebar.slider("Top N autisti", min_value=3, max_value=20, value=10)
    top_stats = stats.head(top_n)
    st.dataframe(top_stats)
    # Grafico a barre interattivo Totale
    st.subheader(f"Top {top_n} Autisti per Totale Compenso")
    bar_tot = (
        alt.Chart(top_stats)
        .mark_bar()
        .encode(
            x=alt.X('Conducente:N', sort='-y'),
            y=alt.Y('Totale:Q'),
            tooltip=[
                alt.Tooltip('Conducente:N', title='Autista'),
                alt.Tooltip('Totale:Q', title='Totale (€)'),
                alt.Tooltip('Media:Q', title='Media (€)'),
                alt.Tooltip('Viaggi:Q', title='N. Viaggi')
            ]
        )
    )
    st.altair_chart(bar_tot, use_container_width=True)
    # Grafico a barre interattivo Media
    st.subheader(f"Top {top_n} Autisti per Media Compenso")
    bar_mean = (
        alt.Chart(top_stats)
        .mark_bar()
        .encode(
            x=alt.X('Conducente:N', sort='-y'),
            y=alt.Y('Media:Q'),
            tooltip=[
                alt.Tooltip('Conducente:N', title='Autista'),
                alt.Tooltip('Totale:Q', title='Totale (€)'),
                alt.Tooltip('Media:Q', title='Media (€)'),
                alt.Tooltip('Viaggi:Q', title='N. Viaggi')
            ]
        )
    )
    st.altair_chart(bar_mean, use_container_width=True)

# Note:
# - Gestione completa dei compensi: conversione e NaN.
# - Collegamento diretto di Costo_Num a Conducente.
# - Grafici interattivi per Totale e Media compenso.
