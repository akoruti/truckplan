import streamlit as st
import pandas as pd
import numpy as np
from PIL import Image

# Try to import pytesseract for OCR; if unavailable, disable OCR functionality
try:
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --- Config ---
st.set_page_config(page_title="Programmazione Viaggi", layout="wide")

st.title("Programmazione Viaggi Autista")
st.markdown("Tutte le regole di layout, riga totale, costi, selezione e OCR (se disponibile) sono applicate automaticamente.")

# --- Funzione OCR dati autista ---
if OCR_AVAILABLE:
    def estrai_dati_autista_da_immagine(image_file):
        img = Image.open(image_file)
        testo = pytesseract.image_to_string(img, lang='ita+eng')
        estratti = {
            "Nome autista": "",
            "Inizio settimana": "",
            "Ore guida residue settimana": "",
            "Ore guida residue oggi": "",
            "Guida ininterrotta residua": "",
            "Pausa obbligatoria residua": "",
            "Ultima posizione GPS": ""
        }
        for line in testo.splitlines():
            l = line.lower()
            if "nome" in l or "autista" in l:
                estratti["Nome autista"] = line.split(":")[-1].strip()
            elif "settimana" in l:
                estratti["Inizio settimana"] = line.split(":")[-1].strip()
            elif "residue settimana" in l:
                estratti["Ore guida residue settimana"] = line.split(":")[-1].strip()
            elif "oggi" in l and "guida" in l:
                estratti["Ore guida residue oggi"] = line.split(":")[-1].strip()
            elif "ininterrotta" in l:
                estratti["Guida ininterrotta residua"] = line.split(":")[-1].strip()
            elif "pausa" in l:
                estratti["Pausa obbligatoria residua"] = line.split(":")[-1].strip()
            elif "gps" in l or "posizione" in l:
                estratti["Ultima posizione GPS"] = line.split(":")[-1].strip()
        return estratti
else:
    def estrai_dati_autista_da_immagine(image_file):
        st.warning("OCR non disponibile: installa pytesseract per abilitare l'estrazione.")
        return {}

# --- Dati Autista (Sidebar) ---
st.sidebar.header("Dati Autista")

if OCR_AVAILABLE:
    uploaded_image = st.sidebar.file_uploader("Carica screenshot dati autista (jpg/png)", type=["jpg", "jpeg", "png"] )
    dati_autista = {}
    if uploaded_image:
        with st.spinner("Estrazione dati da immagine..."):
            dati_autista = estrai_dati_autista_da_immagine(uploaded_image)
        st.sidebar.success("Dati autista estratti dall'immagine!")
else:
    dati_autista = {}

autista_nome = st.sidebar.text_input("Nome autista", dati_autista.get("Nome autista", "S.Pituscan"))
in
izione_settimana = st.sidebar.text_input("Inizio settimana lavorativa", dati_autista.get("Inizio settimana", "2025-07-09"))
ora_inizio_sett = st.sidebar.text_input("Ora inizio settimana", dati_autista.get("Ora inizio settimana","07:00"))
ore_guida_sett = st.sidebar.text_input("Ore guida residue settimana", dati_autista.get("Ore guida residue settimana","56"))
ore_guida_giorno = st.sidebar.text_input("Ore guida residue oggi", dati_autista.get("Ore guida residue oggi","9"))
tempo_guida_ininterrotta = st.sidebar.text_input("Guida ininterrotta residua (min)", dati_autista.get("Guida ininterrotta residua","270"))
pausa_necessaria = st.sidebar.text_input("Pausa obbligatoria residua (min)", dati_autista.get("Pausa obbligatoria residua","45"))
posizione_gps = st.sidebar.text_input("Ultima posizione GPS (lat, lon)", dati_autista.get("Ultima posizione GPS","45.7636166, 10.9984833"))

st.sidebar.markdown("---")
st.sidebar.write(f"**Autista:** {autista_nome}")
st.sidebar.write(f"Posizione GPS: {posizione_gps}")
st.sidebar.write(f"Inizio settimana: {inizio_settimana} {ora_inizio_sett}")
st.sidebar.write(f"Ore guida residue settimana: {ore_guida_sett}")
st.sidebar.write(f"Ore guida residue oggi: {ore_guida_giorno}")
st.sidebar.write(f"Guida ininterrotta residua: {tempo_guida_ininterrotta} min")
st.sidebar.write(f"Pausa obbligatoria residua: {pausa_necessaria} min")

# --- Carica dati viaggi ---
st.subheader("1. Carica i viaggi disponibili")
uploaded_file = st.file_uploader("Carica file CSV o Excel", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    df = pd.DataFrame()

# --- Parametri costi ---
st.sidebar.header("Parametri costi")
prezzo_gasolio = st.sidebar.number_input("Prezzo gasolio €/l", 1.0, 3.0, 1.69, step=0.01)
consumo_km_l = st.sidebar.number_input("Consumo medio (km/l)", 2.0, 6.0, 3.5, step=0.1)
st.sidebar.markdown("*Pedaggi stimati manualmente, aggiornali se hai dati precisi.*")

# --- Calcolo costi ---
def stima_carburante(d, km_l, p): return round(d/km_l*p,2)
if "Distanza" in df.columns and "Compenso (€)" in df.columns:
    if "Carburante (€)" not in df.columns:
        df["Carburante (€)"] = df["Distanza"].apply(lambda x: stima_carburante(x, consumo_km_l, prezzo_gasolio))
    if "Pedaggi (€)" not in df.columns:
        df["Pedaggi (€)"] = 0
    df["Totale costi (€)"] = df["Carburante (€)"] + df["Pedaggi (€)"]

# --- Tabella Programmazione ---
st.subheader("2. Programmazione Viaggi (modificabile)")
if df.empty:
    st.info("Carica un file o inserisci i viaggi manualmente con il tasto + nella tabella.")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# --- Riga Totale ---
if not edited_df.empty:
    tot = edited_df.copy()
    tot_row = {col: "" for col in tot.columns}
    tot_row["Codice Viaggio"] = "TOTALE"
    tot_row["Distanza"] = tot["Distanza"].sum()
    tot_row["Compenso (€)"] = tot["Compenso (€)"].sum()
    tot_row["€/km"] = round(tot["Compenso (€)"].sum()/tot["Distanza"].sum(),2) if tot["Distanza"].sum() else ""
    if "Carburante (€)" in tot.columns:
        tot_row["Carburante (€)"] = tot["Carburante (€)"].sum()
    if "Pedaggi (€)" in tot.columns:
        tot_row["Pedaggi (€)"].sum()
    if "Totale costi (€)" in tot.columns:
        tot_row["Totale costi (€)" ] = tot["Totale costi (€)"].sum()
    full = pd.concat([tot, pd.DataFrame([tot_row])], ignore_index=True)
    st.dataframe(full, use_container_width=True)

# --- Esporta CSV ---
st.download_button("Scarica CSV", data=full.to_csv(index=False), file_name="programmazione_viaggi.csv")

st.success("App pronta! Moduli OCR e regole applicate.")
