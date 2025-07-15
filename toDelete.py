import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Auto‐refresh solo per clock/highlight ---
st_autorefresh(interval=1000, key="refresh")

# --- Ordine desiderato delle colonne ---
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
]

# --- Rinomina colonne da Google Sheets ---
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO":     "DATA ORA ARRIVO",
}

# --- Live clock in fuso Europa/Roma ---
now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
st.markdown("## 🕒 Data e ora attuali (Europa/Roma)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M')}**")  # arrotondato al minuto

st.divider()
st.title("Visualizzazione Viaggi (tutte le righe + highlight)")

# --- Mantieni il DataFrame in session_state ---
if "df" not in st.session_state:
    st.session_state.df = None

# --- Upload CSV ---
uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if uploaded_file:
    df = pd](#)

