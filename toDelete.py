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

# Mappatura per rinominare le colonne
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- LIVE CLOCK ---
st.markdown("## 🕒 Data e ora attuali")
now = datetime.datetime.now()
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizza e filtra le date di partenza")

# --- Uploader CSV ---
uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if not uploaded_file:
    st.info("📂 Nessun file caricato. Carica un CSV per procedere.")
    st.stop()

# --- Caricamento dati ---
df = pd.read_csv(uploaded_file)

# --- Visualizza l'intero contenuto caricato ---
st.subheader("Dati caricati (tutti)")
st.dataframe(df)

# --- Rinomina e riordina colonne ---
df = df.rename(columns=rename_dict)
rest_columns = [c for c in df.columns if c not in desired_order]
ordered_columns = [c for c in desired_order if c in df.columns] + rest_columns
df = df[ordered_columns]

# --- Parsing "DATA ORA PARTENZA" in formato europeo ---
if "DATA ORA PARTENZA" in df.columns:
    df["DATA ORA PARTENZA"] = pd.to_datetime(
        df["DATA ORA PARTENZA"],
        dayfirst=True,
        errors="coerce"
    )
else:
    st.error("La colonna 'DATA ORA PARTENZA' non è stata trovata.")
    st.stop()

# --- Selettore intervallo di date (formato europeo) ---
st.subheader("🔍 Filtra per intervallo di date di partenza")
valid_dates = df["DATA ORA PARTENZA"].dt.date.dropna()
default_start = valid_dates.min() if not valid_dates.empty else now.date()
default_end   = valid_dates.max() if not valid_dates.empty else now.date()

start_date = st.date_input(
    "Data di inizio",
    value=default_start,
    format="DD/MM/YYYY",
    key="start_date"
)
end_date = st.date_input(
    "Data di fine",
    value=default_end,
    format="DD/MM/YYYY",
    key="end_date"
)

if start_date > end_date:
    st.error("La data di inizio deve essere minore o uguale alla data di fine.")
    st.stop()

# --- Filtraggio dei dati ---
df["SOLO DATA"] = df["DATA ORA PARTENZA"].dt.date
mask = (df["SOLO DATA"] >= start_date) & (df["SOLO DATA"] <= end_date)
filtered_df = df[mask].drop(columns=["SOLO DATA"])

# --- Visualizzazione risultati ---
st.subheader("Risultato del filtro")
if filtered_df.empty:
    st.warning(
        f"Nessuna partenza trovata tra "
        f"{start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}."
    )
st.dataframe(filtered_df)

# --- Download del CSV filtrato ---
buffer = io.BytesIO()
filtered_df.to_csv(buffer, index=False)
st.download_button(
    "Scarica CSV filtrato",
    data=buffer.getvalue(),
    file_name=(
        f"dati_{start_date.strftime('%Y%m%d')}_"
        f"{end_date.strftime('%Y%m%d')}.csv"
    ),
    mime="text/csv"
)


