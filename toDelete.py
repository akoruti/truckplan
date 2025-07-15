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
    # altre colonne se vuoi
]

rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# LIVE CLOCK
st.markdown("## 🕒 Data e ora attuali")
now = datetime.datetime.now()
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizza CSV con colonne nell’ordine desiderato")

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    rest_columns = [col for col in df.columns if col not in desired_order]
    ordered_columns = [col for col in desired_order if col in df.columns] + rest_columns
    df = df[ordered_columns]

    # --- Filtra per DATA ORA PARTENZA del giorno corrente ---
    if 'DATA ORA PARTENZA' in df.columns:
        # Prova a estrarre la sola data (no ora) come stringa
        df['DATA SOLO DATA'] = df['DATA ORA PARTENZA'].astype(str).str.extract(r'(\d{2}/\d{2}/\d{4})')
        today_str = now.strftime('%d/%m/%Y')
        mask_today = df['DATA SOLO DATA'] == to_

