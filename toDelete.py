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
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizza e filtra per intervallo di date di partenza (formato europeo)")

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

# Parsing "DATA ORA PARTENZA" come datetime europeo
if "DATA ORA PARTENZA" in df.columns:
    df["DATA ORA PARTENZA"] = pd.to_datetime(
        df["DATA ORA PARTENZA"],
        dayfirst=True,
        errors="coerce",
    )
else:
    st.error("La colonna 'DATA ORA PARTENZA' non è stata trovata.")
    st.stop()

# --- Selettore intervallo di date ---
st.subheader("🔍 Scegli intervallo di date di partenza")
# Estraiamo le date valide (drop NA) prima di calcolare min/max
valid_dates = df["DATA ORA PARTENZA"].dt.date.dropna()
default_start = valid_dates.min() if not valid_dates.empty else now.date()
default_end   = valid_dates.max() if not valid_dates.empty else now.date()

start_date, end_date = st.date_input(
    "Intervallo",
    value=(default_start, default_end),
    format="DD/MM/YYYY",
)

# Verifica che start_date ≤ end_date
if start_date > end_date:
    st.error("La data di inizio deve essere minore o uguale alla data di fine.")
    st.stop()

# Filtra per intervallo
df["SOLO DATA"] = df["DATA ORA PARTENZA"].dt.date
mask = (df["SOLO DATA"] >= start_date) & (df["SOLO DATA"] <= end_date)
filtered_df = df[mask].drop(columns=["SOLO DATA"])

# Messaggio se non ci sono righe
if filtered_df.empty:
    st.warning(f"Nessuna partenza trovata tra {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}.")

# --- Visualizzazione e download ---
st.subheader("Tabella filtrata e riordinata")
st.dataframe(filtered_df)

buffer = io.BytesIO()
filtered_df.to_csv(buffer, index=False)
st.download_button(
    "Scarica CSV filtrato",
    data=buffer.getvalue(),
    file_name=f"dati_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv",
    mime="text/csv",
)
