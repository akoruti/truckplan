import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo  # Python 3.9+

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Ordine delle colonne desiderato ---
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

# --- LIVE CLOCK in fuso Italia ---
now = datetime.datetime.now(ZoneInfo("Europe/Rome"))
st.markdown("## 🕒 Data e ora attuali (Europa/Roma)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("Visualizzazione Viaggi (prime oggi, highlight partenza)")

# --- Mantieni il DataFrame in memoria ---
if "df" not in st.session_state:
    st.session_state.df = None

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    st.session_state.df = df

# --- Elaborazione dati se presenti ---
if st.session_state.df is not None:
    df = st.session_state.df.copy()

    # 1) Riordina colonne
    rest_cols   = [c for c in df.columns if c not in desired_order]
    ordered_cols= [c for c in desired_order if c in df.columns] + rest_cols
    df = df[ordered_cols]

    # 2) Crea colonna datetime per il confronto
    df["__DEP_DT__"] = (
        pd.to_datetime(df["DATA ORA PARTENZA"], dayfirst=True, errors="coerce")
          .dt.tz_localize(ZoneInfo("Europe/Rome"), nonexistent="NaT", ambiguous="NaT")
    )

    # 3) Ordina decrescente per DATA ORA PARTENZA
    df = df.sort_values("__DEP_DT__", ascending=False)

    # 4) Funzione per evidenziare la riga di partenza
    def highlight_departure(row):
        dt = row["__DEP_DT__"]
        if pd.notna(dt):
            # se la differenza con ora corrente è < 60s
            diff = abs((dt - datetime.datetime.now(ZoneInfo("Europe/Rome"))).total_seconds())
            if diff < 60:
                return ["background-color: lightgreen"] * len(row)
        return [""] * len(row)

    # 5) Applica lo stile e nascondi la colonna interna
    styled = (
        df.style
          .apply(highlight_departure, axis=1)
          .hide(columns="__DEP_DT__")
    )

    # 6) Mostra la tabella styled
    st.subheader(f"Tabella – prime le partenze del {now.strftime('%d/%m/%Y')}")
    st.dataframe(styled, use_container_width=True)

    # 7) Pulsante per scaricare il CSV riordinato (senza la colonna interna)
    out = io.BytesIO()
    df.drop(columns="__DEP_DT__").to_csv(out, index=False)
    st.download_button(
        "📥 Scarica CSV ordinato e filtrato",
        data=out.getvalue(),
        file_name="viaggi_riordinati.csv",
        mime="text/csv"
    )
else:
    st.info("⏳ In attesa del caricamento di un CSV.")

# --- Auto-reload della pagina ogni secondo per aggiornare il clock e il highlight ---
st.markdown(
    """
    <script>
      setTimeout(() => { window.location.reload(); }, 1000);
    </script>
    """,
    unsafe_allow_html=True,
)


