import streamlit as st
import pandas as pd
import io
import datetime
from zoneinfo import ZoneInfo

# --- Configurazione pagina ---
st.set_page_config(page_title="Gestione Viaggi", layout="wide")

# --- Ordine desiderato delle colonne ---
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
]

# --- Rinomina colonne ---
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

# --- Ora corrente con fuso Europa/Roma ---
now = datetime.datetime.now(ZoneInfo("Europe/Roma"))
now_str = now.strftime('%d/%m/%Y %H:%M')

# Mostra orologio live
st.markdown("## 🕒 Data e ora attuali (Italia)")
st.info(f"**{now.strftime('%d/%m/%Y %H:%M:%S')}**")

st.divider()
st.title("📅 Visualizzazione Viaggi con Highlight Partenza")

# --- Session State per conservare dati ---
if "df" not in st.session_state:
    st.session_state.df = None

# --- Upload CSV ---
uploaded_file = st.file_uploader("📁 Carica un file CSV", type="csv")
if uploaded_file:
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    st.session_state.df = df

# --- Elaborazione e visualizzazione dati ---
if st.session_state.df is not None:
    df = st.session_state.df.copy()

    # Riordina colonne
    rest_cols = [col for col in df.columns if col not in desired_order]
    ordered_cols = [col for col in desired_order if col in df.columns] + rest_cols
    df = df[ordered_cols]

    # Converti DATA ORA PARTENZA in datetime con fuso orario
    df['PARTENZA_DT'] = pd.to_datetime(
        df["DATA ORA PARTENZA"], dayfirst=True, errors='coerce'
    ).dt.tz_localize(ZoneInfo("Europe/Roma"), nonexistent='NaT', ambiguous='NaT')

    # Ordina decrescente per DATA ORA PARTENZA
    df = df.sort_values(by='PARTENZA_DT', ascending=False)

    # Evidenzia in verde se data e ora corrente coincidono esattamente al minuto
    df['PARTENZA_STR'] = df['PARTENZA_DT'].dt.strftime('%d/%m/%Y %H:%M')
    df['highlight'] = df['PARTENZA_STR'] == now_str

    # Funzione per evidenziare la riga
    def highlight_row(row):
        color = 'background-color: lightgreen' if row['highlight'] else ''
        return [color] * (len(row)-2) + ['', '']  # non colorare colonne tecniche

    # Applica styling
    styled_df = df.drop(columns=['PARTENZA_DT', 'highlight']).style.apply(highlight_row, axis=1)

    # Mostra tabella (scrollabile)
    st.subheader("📋 Elenco viaggi:")
    st.dataframe(styled_df, use_container_width=True, height=600)

    # Download CSV aggiornato (senza colonne tecniche)
    output = io.BytesIO()
    df.drop(columns=['PARTENZA_DT', 'highlight']).to_csv(output, index=False)
    st.download_button(
        label="📥 Scarica CSV aggiornato",
        data=output.getvalue(),
        file_name="viaggi_aggiornati.csv",
        mime="text/csv"
    )

else:
    st.info("ℹ️ In attesa di caricamento CSV...")

# --- Auto-refresh della pagina ogni secondo ---
st.markdown(
    """
    <script>
        setTimeout(function(){
            window.location.reload(1);
        }, 1000);
    </script>
    """,
    unsafe_allow_html=True
)
