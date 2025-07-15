import streamlit as st
import pandas as pd
import io

# Ordine desiderato delle colonne
desired_order = [
    "AUTISTA",
    "DATA ORA PARTENZA",
    "DATA ORA ARRIVO",
    "PARTENZA",
    "ARRIVO",
    # Puoi aggiungere qui altre colonne se vuoi, oppure lascia che il resto venga dopo
]

# Dizionario per rinominare le colonne come da esigenza
rename_dict = {
    "Unnamed: 0": "DATA ORA PARTENZA",
    "ORARIO": "DATA ORA ARRIVO",
}

st.title("Visualizza CSV con colonne nell’ordine desiderato")

uploaded_file = st.file_uploader("Carica un file CSV", type="csv")

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    
    # Rinomina colonne se necessario
    df = df.rename(columns=rename_dict)
    
    # Costruisci nuovo ordine, le colonne che non sono in desired_order vengono dopo
    rest_columns = [col for col in df.columns if col not in desired_order]
    ordered_columns = [col for col in desired_order if col in df.columns] + rest_columns
    df_ordered = df[ordered_columns]
    
    st.subheader("Tabella riordinata")
    st.dataframe(df_ordered)
    
    # Pulsante per scaricare il file riordinato
    output = io.BytesIO()
    df_ordered.to_csv(output, index=False)
    st.download_button(
        label="Scarica CSV riordinato",
        data=output.getvalue(),
        file_name="dati_riordinati.csv",
        mime="text/csv"
    )
else:
    st.info("Carica un file CSV per visualizzare i dati.")

