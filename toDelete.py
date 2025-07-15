import streamlit as st
import pandas as pd
import io
import datetime

# --- Configurazione colonne ---
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
    # aggiungi qui altre colonne se necessario
]

rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- LIVE CLOCK ---
st.markdown("## 🕒 Data e ora attuali")
now = datetime.datetime.now()
st.info(f"**{now.strftime('%m/%d/%Y %H:%M:%S')}**")  # mostrato in US per coerenza

st.divider()
st.title("Visualizza e filtra per intervallo di date di partenza (formato US)")

# --- Uploader CSV ---
uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if not uploaded_file:
    st.stop()

# --- Caricamento e preprocessing ---
df = pd.read_csv(uploaded_file)
df = df.rename(columns=rename_dict)

# Riordina le colonne
rest_columns = [col for col in df.columns if col not in desired_order]
ordered_columns = [col for col in desired_order if col in df.columns] + rest_columns
df = df[ordered_columns]

# Parsing "DATA ORA PARTENZA" in formato US (MM/DD/YYYY)
if "DATA ORA PARTENZA" in df.columns:
    df["DATA ORA PARTENZA"] = pd.to_datetime(
        df["DATA ORA PARTENZA"],
        dayfirst=False,    # month/day/year
        errors="coerce",
    )
else:
    st.error("La colonna 'DATA ORA PARTENZA' non è stata trovata.")
    st.stop()

# --- Selettore intervallo di date ---
st.subheader("🔍 Scegli intervallo di date di partenza")
# Estrai date valide per default range
valid_dates = df["DATA ORA PARTENZA"].dt.date.dropna()
default_start = valid_dates.min() if not valid_dates.empty else now.date()
default_end   = valid_dates.max() if not valid_dates.empty else now.d_
