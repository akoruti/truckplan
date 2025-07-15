import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo  # Python 3.9+
from streamlit_autorefresh import st_autorefresh  # pip install streamlit-autorefresh

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Ordine desiderato delle colonne ---
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
    # aggiungi qui altre colonne se serve
]

# --- Mappatura per rinominare colonne ---
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- Auto-refresh del clock (ogni 1 secondo) ---
st_autorefresh(interval=1000, key="refresh_clock")

# --- Live clock in fuso Italia ---
now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
st.markdown("## 🕒 Data e ora attuali (Europa/Roma)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizzazione Viaggi (prime oggi)")

# --- Mantieni il DataFrame in memoria fino a nuovo upload ---
if "df" not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    st.session_state.df = df

# Se c'è un DataFrame in session_state, lo elaboriamo
if st.session_state.df is not None:
    df = st.session_state.df.copy()
    
    # 1) Riordina le colonne
    rest_cols = [c for c in df.columns if c not in desired_order]
    ordered_cols = [c for c in desired_order if c in df.columns] + rest_cols
    df = df[ordered_cols]
    
    # 2) Metti in cima le righe con DATA ORA PARTENZA di oggi (fuso Italia)
    if "DATA ORA PARTENZA" in df.columns:
        df["DATA SOLO"] = (
            pd.to_datetime(df["DATA ORA PARTENZA"], dayfirst=True, errors="coerce")
            .dt.tz_localize(ZoneInfo("Europe/Rome"), nonexistent="NaT", ambiguous="NaT")
            .dt.strftime("%d/%m/%Y")
        )
        today_str = now.strftime("%d/%m/%Y")
        df_today = df[df["DATA SOLO"] == today_str]
        df_rest  = df[df["DATA SOLO"] != today_str]
        df = pd.concat([df_today, df_rest]).drop(columns=["DATA SOLO"])
    
    # 3) Mostra la tabella
    st.subheader(f"Tabella – prime le partenze del {now.strftime('%d/%m/%Y')}")
    st.dataframe(df, use_container_width=True)
    
    # 4) Pulsante per scaricare il CSV riordinato
    out_buffer = io.BytesIO()
    df.to_csv(out_buffer, index=False)
    st.download_button(
        label="📥 Scarica CSV riordinato",
        data=out_buffer.getvalue(),
        file_name="viaggi_riordinati.csv",
        mime="text/csv"
    )
else:
    st.info("⏳ In attesa del caricamento di un CSV.")
