import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Ordine desiderato delle colonne ---
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
    # puoi aggiungere altre colonne qui
]

# --- Rinomina colonne da Google Sheets ---
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- Mostra clock in fuso Italia ---
now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
st.markdown("## 🕒 Data e ora attuali (Europa/Roma)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizzazione Viaggi (prime oggi, highlight partenza)")

# --- Session state per mantenere i dati ---
if "df" not in st.session_state:
    st.session_state.df = None

# --- Caricamento CSV ---
uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    st.session_state.df = df

# --- Elaborazione dati se presenti ---
if st.session_state.df is not None:
    df = st.session_state.df.copy()

    # 1) Riordina colonne
    rest_cols    = [c for c in df.columns if c not in desired_order]
    ordered_cols = [c for c in desired_order if c in df.columns] + rest_cols
    df = df[ordered_cols]

    # 2) Crea datetime di partenza e serie di highlight
   # converte e imposta fuso
dep_dt = (
    pd.to_datetime(df["DATA ORA PARTENZA"], dayfirst=True, errors="coerce")
      .dt.tz_localize(ZoneInfo("Europe/Rome"), nonexistent="NaT", ambiguous="NaT")
)

# formato "gg/mm/aaaa HH:MM"
dep_min = dep_dt.dt.strftime("%d/%m/%Y %H:%M")
now_str = datetime.datetime.now(ZoneInfo("Europe/Rome")).strftime("%d/%m/%Y %H:%M")

# True solo se minuti identici
highlight_flag = dep_min == now_str

    # Booleano: True se differenza < 60 secondi
    now_r = datetime.datetime.now(ZoneInfo("Europe/Rome"))
    highlight_series = (dep_dt - now_r).abs().dt.total_seconds() < 60

    # 3) Ordina decrescente per data partenza
    df["__DEP_SORT__"] = dep_dt
    df = df.sort_values("__DEP_SORT__", ascending=False).drop(columns="__DEP_SORT__")

    # 4) Prepara DataFrame da mostrare (senza colonna interna)
    display_df = df.copy()

    # 5) Funzione di styling
    def highlight_row(row):
        if highlight_series.loc[row.name]:
            return ["background-color: lightgreen"] * len(row)
        return [""] * len(row)

    styled = display_df.style.apply(highlight_row, axis=1)

    # 6) Render della tabella
    st.subheader(f"Tabella – prime le partenze del {now.strftime('%d/%m/%Y')}")
    st.dataframe(styled, use_container_width=True)

    # 7) Download CSV pulito
    buffer = io.BytesIO()
    display_df.to_csv(buffer, index=False)
    st.download_button(
        label="📥 Scarica CSV aggiornato",
        data=buffer.getvalue(),
        file_name="viaggi_riordinati.csv",
        mime="text/csv"
    )
else:
    st.info("⏳ In attesa del caricamento di un CSV.")

# --- Ricarica pagina ogni secondo via JavaScript per aggiornare clock e highlight ---
st.markdown(
    """
    <script>
      setTimeout(() => { window.location.reload(); }, 1000);
    </script>
    """,
    unsafe_allow_html=True
)


