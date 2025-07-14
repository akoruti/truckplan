# app_rejected.py

import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(page_title="Rilevazione Rejected Trips", layout="wide")
st.title("Dashboard Rifiuti Viaggi")

# 1. Upload
uploaded_file = st.file_uploader("Carica il file CSV dei viaggi", type="csv")
if not uploaded_file:
    st.info("Carica un CSV per analizzare i viaggi.")
    st.stop()

df = pd.read_csv(uploaded_file)

# 2. Riepilogo Stati
st.subheader("Overview Stati Viaggi")
status_counts = df['Stato'].value_counts().reset_index()
status_counts.columns = ["Stato", "Conteggio"]
st.dataframe(status_counts)

# 3. Regola per “rejected”
df['IsRejected'] = (df['Stato'] == 'PLANNED') & (df['Corriere'] == 'ADASR')
rej_counts = df['IsRejected'].value_counts().rename({False:'Altro', True:'Rejected'})
st.subheader("Conteggio Rejected (PLANNED+ADASR)")
st.bar_chart(rej_counts)

# 4. Dettagli dei Rejected
st.subheader("Dettagli Viaggi Rejected")
rejected_df = df[df['IsRejected']]
# Seleziona le colonne chiave
cols = ['Trip ID', 'Corriere', 'È un camion CPT', 'Filtro furgone', 'CPT']
st.dataframe(rejected_df[cols].reset_index(drop=True))

# 5. Grafico a torta % camion CPT nei rejected
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



