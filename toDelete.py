# app_rejected.py

import streamlit as st
import pandas as pd
import altair as alt

# Configurazione pagina
st.set_page_config(page_title="Rilevazione Rejected Trips", layout="wide")
st.title("Dashboard Rifiuti Viaggi")

# 1. Upload del file
uploaded_file = st.file_uploader("Carica il file CSV dei viaggi", type="csv")
if not uploaded_file:
    st.info("Carica un CSV per analizzare i viaggi.")
    st.stop()

df = pd.read_csv(uploaded_file)

# 2. Parsing della sequenza di strutture in Origine e Destinazione
if 'Sequenza delle strutture' in df.columns:
    seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
    df['Origine'] = seq[0]
    df['Destinazione'] = seq[1]

# 3. Estrazione targa dal campo 'ID Veicolo' dopo il suffisso 'OTHR-'
if 'ID Veicolo' in df.columns:
    df['Targa'] = df['ID Veicolo'].astype(str).str.extract(r'OTHR-(.*)')

# 4. Filtra per Stato
st.sidebar.subheader("Filtra per Stato")
stato_options = ['COMPLETED', 'CANCELLED', 'PLANNED']
selected_states = st.sidebar.multiselect(
    "Seleziona stati da visualizzare", stato_options, default=stato_options
)
filtered_df = df[df['Stato'].isin(selected_states)]

# 5. Riepilogo Stati (post-filtro)
st.subheader("Overview Stati Viaggi")
status_counts = filtered_df['Stato'].value_counts().reindex(stato_options, fill_value=0).reset_index()
status_counts.columns = ["Stato", "Conteggio"]
st.dataframe(status_counts)

# 6. Identificazione Rejected
# Consideriamo ‘PLANNED’ + ‘ADASR’ come rejected
df['IsRejected'] = (df['Stato'] == 'PLANNED') & (df['Corriere'] == 'ADASR')
rejected_df = df[df['IsRejected']]

# 7. Conteggio Rejected
st.subheader("Numero di Rejected (PLANNED+ADASR)")
st.metric("Viaggi Rejected", rejected_df.shape[0])

# 8. Dettagli Viaggi Rejected
st.subheader("Dettagli Viaggi Rejected")
cols = [
    'ID VR', 'Stato', 'Corriere', 'Conducente', 'Origine', 'Destinazione',
    'Sequenza delle strutture', 'Targa', 'È un camion CPT', 'Filtro furgone', 'CPT', 'Costo stimato'
]
cols = [c for c in cols if c in df.columns]
st.dataframe(rejected_df[cols].reset_index(drop=True))

# 9. Compenso medio dei Rejected
if 'Costo stimato' in rejected_df.columns:
    # Converti a numerico gestendo valori non numerici
    costs = pd.to_numeric(rejected_df['Costo stimato'], errors='coerce')
    avg_cost = costs.mean()
    st.subheader("Compenso Medio dei Rejected")
    st.metric("Valore Medio", f"{avg_cost:.2f}")

# 10. Grafico: Percentuale Camion CPT nei Rejected
st.subheader("Percentuale Camion CPT fra i Rejected")
pie = (
    rejected_df['È un camion CPT']
    .value_counts(normalize=True)
    .rename(index={True:'Camion', False:'Non Camion'})
    .reset_index()
    .rename(columns={'index':'Categoria','È un camion CPT':'Percentuale'})
)
chart = alt.Chart(pie).mark_arc(innerRadius=50).encode(
    theta=alt.Theta(field="Percentuale", type="quantitative"),
    color=alt.Color(field="Categoria", type="nominal"),
    tooltip=["Categoria", "Percentuale"]
)
st.altair_chart(chart, use_container_width=True)

# 11. Grafico a barre: Distribuzione Viaggi per Stato Post-Filtro
st.subheader("Distribuzione Viaggi per Stato")
bar = alt.Chart(status_counts).mark_bar().encode(
    x=alt.X('Stato', sort=stato_options),
    y='Conteggio',
    color='Stato'
)
st.altair_chart(bar, use_container_width=True)

# 12. Analisi Compenso per Conducente
if 'Conducente' in rejected_df.columns and 'Costo stimato' in rejected_df.columns:
    # Raggruppa e calcola totali convertendo a numerico
    rejected_df['Costo_Num'] = pd.to_numeric(rejected_df['Costo stimato'], errors='coerce')
    driver_stats = (
        rejected_df.groupby('Conducente')['Costo_Num']
        .agg(Totale='sum', Media='mean', Conteggio='count')
        .reset_index()
        .sort_values('Totale', ascending=False)
    )
    st.subheader("Compenso Totale per Conducente")
    top_n = st.sidebar.slider("Mostra top N conducenti", min_value=3, max_value=20, value=10)
    top_stats = driver_stats.head(top_n)
    st.dataframe(top_stats)
    st.subheader(f"Top {top_n} Conducenti per Compenso Totale")
    bar_driver = (
        alt.Chart(top_stats)
        .mark_bar()
        .encode(
            x=alt.X('Conducente', sort='-y'),
            y='Totale',
            tooltip=['Conducente', 'Totale', 'Media', 'Conteggio']
        )
    )
    st.altair_chart(bar_driver, use_container_width=True)

# Note:
# - Gestito conversione del 'Costo stimato' a numerico per evitare errori.
# - Rimosso il vecchio calcolo diretto .mean() su stringhe.
# - Aggiunta colonna temporanea 'Costo_Num' per l'analisi per conducente.
