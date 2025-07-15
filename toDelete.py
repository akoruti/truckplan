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
    # aggiungi qui altre colonne se ti servono ancora
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
st.title("Visualizza e filtra per intervallo di date di partenza")

# --- Uploader CSV ---
uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if not uploaded_file:
    st.info("📂 Nessun file caricato. Usa il pulsante qui sopra per selezionare il CSV.")
    st.stop()

# --- 1) Caricamento raw e preview ---
df = pd.read_csv(uploaded_file)
st.subheader("Anteprima dati (raw)")
st.dataframe(df.head(5))

# --- 2) Rinomina colonne e reorder ---
df = df.rename(columns=rename_dict)
# metti le desired_order in testa, poi il resto
rest_columns = [c for c in df.columns if c not in desired_order]
ordered_columns = [c for c in desired_order if c in df.columns] + rest_columns
df = df[ordered_columns]
st.subheader("Anteprima dopo rename e riordino colonne")
st.dataframe(df.head(5))

# --- 3) Parsing date in formato europeo (dd/mm/yyyy) ---
if "DATA ORA PARTENZA" in df.columns:
    df["DATA ORA PARTENZA"] = pd.to_datetime(
        df["DATA ORA PARTENZA"],
        dayfirst=True,
        errors="coerce"
    )
else:
    st.error("La colonna 'DATA ORA PARTENZA' non è stata trovata.")
    st.stop()

# --- 4) Selettore intervallo in formato US (MM/DD/YYYY) ---
st.subheader("🔍 Filtra per intervallo di date di partenza (MM/DD/YYYY)")
valid_dates = df["DATA ORA PARTENZA"].dt.date.dropna()
default_start = valid_dates.min() if not valid_dates.empty else now.date()
default_end = valid_dates.max() if not valid_dates.empty else now.date()

start_date = st.date_input(
    "Select start date",
    value=default_start,
    format="MM/DD/YYYY",
    key="start_date"
)
end_date = st.date_input(
    "Select end date",
    value=default_end,
    format="MM/DD/YYYY",
    key="end_date"
)
if start_date > end_date:
    st.error("The start date must be on or before the end date.")
    st.stop()

# --- 5) Filtro e visualizzazione finale ---
df["SOLO DATA"] = df["DATA ORA PARTENZA"].dt.date
mask = (df["SOLO DATA"] >= start_date) & (df["SOLO DATA"] <= end_date)
filtered_df = df[mask].drop(columns=["SOLO DATA"])

if filtered_df.empty:
    st.warning(
        f"No departures found between "
        f"{start_date.strftime('%m/%d/%Y')} and {end_date.strftime('%m/%d/%Y')}."
    )
else:
    st.subheader("Risultato del filtro")
st.dataframe(filtered_df)

# --- 6) Download del CSV filtrato ---
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



