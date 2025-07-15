import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo
from streamlit_autorefresh import st_autorefresh

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Auto‐refresh ogni secondo ---
st_autorefresh(interval=1000, key="refresh")

# --- Ordine delle colonne desiderato ---
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
    "ORARIO": "DATA ORA ARRIVO",
}

# --- Live clock in fuso Europa/Roma ---
now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
st.markdown("## 🕒 Data e ora attuali (Europa/Roma)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M')}**")  # arrotondato al minuto

st.divider()
st.title("Visualizzazione Viaggi (tutte le righe + highlight partenza)")

# --- Mantieni il DataFrame in session_state ---
if "df" not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    st.session_state.df = df

if st.session_state.df is not None:
    df = st.session_state.df.copy()

    # 1) Riordina colonne
    other_cols = [c for c in df.columns if c not in desired_order]
    cols = [c for c in desired_order if c in df.columns] + other_cols
    df = df[cols]

    # 2) Confronto arrotondato al minuto
    dep_dt = (
        pd.to_datetime(df["DATA ORA PARTENZA"], dayfirst=True, errors="coerce")
          .dt.tz_localize(ZoneInfo("Europe/Rome"), nonexistent="NaT", ambiguous="NaT")
    )
    dep_min = dep_dt.dt.strftime("%d/%m/%Y %H:%M")
    now_str = now.strftime("%d/%m/%Y %H:%M")
    highlight_flag = dep_min == now_str

    # 3) Ordina decrescente su DATA ORA PARTENZA
    df["__SORT__"] = dep_dt
    df = df.sort_values("__SORT__", ascending=False).drop(columns="__SORT__")

    # 4) Funzione di styling
    def hl_row(row):
        if highlight_flag.loc[row.name]:
            return ["background-color: lightgreen"] * len(row)
        return [""] * len(row)

    styled = df.style.apply(hl_row, axis=1)

    # 5) Mostra tabella scrollabile
    st.subheader(f"Tutte le partenze – {now.strftime('%d/%m/%Y')}")
    st.dataframe(styled, use_container_width=True, height=600)

    # 6) Download CSV
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    st.download_button("📥 Scarica CSV", buf.getvalue(), "viaggi.csv", "text/csv")

else:
    st.info("⏳ Carica un CSV per visualizzare i viaggi.")


