import streamlit as st
import pandas as pd
import io
import datetime

# Ordine desiderato delle colonne
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
st.title("Visualizza CSV con colonne nell’ordine desiderato (prime oggi)")

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")

if uploaded_file is not None:
    # 1) Carica e rinomina colonne
    df = pd.read_csv(uploaded_file)
    df = df.rename(columns=rename_dict)
    # 2) Applica l'ordine desiderato
    rest_columns = [col for col in df.columns if col not in desired_order]
    ordered_columns = [col for col in desired_order if col in df.columns] + rest_columns
    df = df[ordered_columns]

    # 3) Metti in cima le righe di oggi
    if "DATA ORA PARTENZA" in df.columns:
        # Estrai la sola data (gg/mm/aaaa)
        df["DATA SOLO DATA"] = df["DATA ORA PARTENZA"].astype(str).str.extract(r"(\d{2}/\d{2}/\d{4})")
        today_str = now.strftime("%d/%m/%Y")
        mask_today = df["DATA SOLO DATA"] == today_str
        df_today = df[mask_today]
        df_rest = df[~mask_today]
        df = pd.concat([df_today, df_rest]).drop(columns=["DATA SOLO DATA"])

    # 4) Mostra la tabella
    st.subheader(f"Tabella – prime le partenze del {now.strftime('%d/%m/%Y')}")
    st.dataframe(df)

    # 5) Pulsante per scaricare il CSV riordinato
    output = io.BytesIO()
    df.to_csv(output, index=False)
    st.download_button(
        label="Scarica CSV riordinato",
        data=output.getvalue(),
        file_name="dati_riordinati.csv",
        mime="text/csv"
    )
else:
    st.info("Carica un file CSV per visualizzare i dati.")
