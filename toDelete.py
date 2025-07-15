import streamlit as st
import pandas as pd
import io
import datetime

# Ordine desiderato delle colonne
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
    # aggiungi qui eventuali altre colonne preferite
]

rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- LIVE CLOCK ---
st.markdown("## 🕒 Data e ora attuali")
now = datetime.datetime.now()
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizza CSV con colonne nell’ordine desiderato (prima le partenze di oggi)")

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    rest_columns = [col for col in df.columns if col not in desired_order]
    ordered_columns = [col for col in desired_order if col in df.columns] + rest_columns
    df = df[ordered_columns]

    # --- Filtra per DATA ORA PARTENZA del giorno corrente ---
    if 'DATA ORA PARTENZA' in df.columns:
        # Estrae solo la data (gg/mm/aaaa) dall'inizio della ce
