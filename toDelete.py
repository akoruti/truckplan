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

# 4. Parsing colonne utili
if 'Sequenza delle strutture' in df.columns:
    seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
    df['Origine'], df['Destinazione'] = seq[0], seq[1]
if 'ID Veicolo' in df.columns:
    df['Targa'] = df['ID Veicolo'].astype(str).str.extract(r'OTHR-(.*)')

# 5. Estrazione compensi e collegamento ad autisti
if 'Costo stimato' in df.columns:
    df['Costo_Num'] = pd.to_numeric(df['Costo stimato'], errors='coerce')
else:
    df['Costo_Num'] = pd.NA

# 6. Filtri principali
st.sidebar.subheader("Filtri")
stato_options = df['Stato'].unique().tolist() if 'Stato' in df.columns else []
selected_states = st.sidebar.multiselect("Stato viaggi", stato_options, default=stato_options)
carriers = df['Corriere'].unique().tolist() if 'Corriere' in df.columns else []
selected_carriers = st.sidebar.multiselect("Corriere", carriers, default=carriers)
filtered_df = df[df['Stato'].isin(selected_states) & df['Corriere'].isin(selected_carriers)]

# 7. Overview viaggi
st.subheader("Overview Stati Viaggi")
state_counts = filtered_df['Stato'].value_counts().reset_index()
state_counts.columns = ['Stato', 'Conteggio']
st.dataframe(state_counts)

# 8. Dettagli di tutti i viaggi
st.subheader("Dettagli di Tutti i Viaggi")
cols = [
    'ID VR', 'Stato', 'Corriere', 'Conducente', 'Origine', 'Destinazione',
    'Sequenza delle strutture', 'Targa', 'È un camion CPT', 'Filtro furgone',
    'CPT', 'Costo stimato'
]
cols = [c for c in cols if c in filtered_df.columns]
st.dataframe(filtered_df[cols].reset_index(drop=True))

# 9. Analisi compensi generali
st.subheader("Compenso Medio e Totale di Tutti i Viaggi")
avg_all = filtered_df['Costo_Num'].mean()
tot_all = filtered_df['Costo_Num'].sum()
st.metric("Compenso Medio (€)", f"{avg_all:.2f}")
st.metric("Compenso Totale (€)", f"{tot_all:.2f}")

# 10. Grafici interattivi
# 10.1: Percentuale Camion CPT
st.subheader("Percentuale Camion CPT tra i Viaggi")
pie_data = (
    filtered_df['È un camion CPT']
    .value_counts(normalize=True)
    .rename(index={True:'Camion', False:'Non Camion'})
    .reset_index()
    .rename(columns={'index':'Categoria', 'È un camion CPT':'Percentuale'})
)
pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
    theta=alt.Theta('Percentuale:Q'),
    color=alt.Color('Categoria:N'),
    tooltip=[alt.Tooltip('Categoria:N', title='Categoria'), alt.Tooltip('Percentuale:Q', title='Percentuale')]
)
st.altair_chart(pie_chart, use_container_width=True)

# 10.2: Distribuzione Viaggi per Stato
st.subheader("Distribuzione Viaggi per Stato")
bar_chart = alt.Chart(state_counts).mark_bar().encode(
    x=alt.X('Stato:N', sort=state_counts['Stato'].tolist()),
    y=alt.Y('Conteggio:Q'),
    color=alt.Color('Stato:N')
).properties(width=600)
st.altair_chart(bar_chart, use_container_width=True)

# 11. Analisi compensi per autista
if 'Conducente' in filtered_df.columns:
    st.subheader("Compenso Totale e Medio per Autista")
    stats = (
        filtered_df.groupby('Conducente')['Costo_Num']
        .agg(Totale='sum', Media='mean', Viaggi='count')
        .reset_index()
        .sort_values('Totale', ascending=False)
    )
    top_n = st.sidebar.slider("Top N autisti", min_value=3, max_value=20, value=10)
    top_stats = stats.head(top_n)
    st.dataframe(top_stats)
    # Grafico Totale
    bar_tot = alt.Chart(top_stats).mark_bar().encode(
        x=alt.X('Conducente:N', sort='-y'),
        y=alt.Y('Totale:Q'),
        tooltip=[
            alt.Tooltip('Conducente:N', title='Autista'),
            alt.Tooltip('Totale:Q', title='Totale (€)'),
            alt.Tooltip('Media:Q', title='Media (€)'),
            alt.Tooltip('Viaggi:Q', title='N. Viaggi')
        ]
    )
    st.subheader(f"Top {top_n} Autisti per Totale Compenso")
    st.altair_chart(bar_tot, use_container_width=True)
    # Grafico Media
    bar_mean = alt.Chart(top_stats).mark_bar().encode(
        x=alt.X('Conducente:N', sort='-y'),
        y=alt.Y('Media:Q'),
        tooltip=[
            alt.Tooltip('Conducente:N', title='Autista'),
            alt.Tooltip('Totale:Q', title='Totale (€)'),
            alt.Tooltip('Media:Q', title='Media (€)'),
            alt.Tooltip('Viaggi:Q', title='N. Viaggi')
        ]
    )
    st.subheader(f"Top {top_n} Autisti per Media Compenso")
    st.altair_chart(bar_mean, use_container_width=True)

# Note:
# - Rimosse le anteprime dati su richiesta.
# - Tutte le altre funzionalità rimangono invariate.
