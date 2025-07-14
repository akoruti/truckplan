
import streamlit as st
import pandas as pd
import numpy as np

# --- Config ---
pip install pytesseract pillow
sudo apt-get install tesseract-ocr  # (su Ubuntu/Debian) oppure installa Tesseract per Windows/Mac
import pytesseract
from PIL import Image

def estrai_dati_autista_da_immagine(image_file):
    """Legge i dati autista da una immagine tramite OCR e restituisce un dizionario"""
    img = Image.open(image_file)
    testo = pytesseract.image_to_string(img, lang='ita+eng')
    # SEMPLICE parsing: cerca pattern comuni. Migliorabile con regex!
    estratti = {
        "Nome autista": "",
        "Inizio settimana": "",
        "Ore guida residue settimana": "",
        "Ore guida residue oggi": "",
        "Guida ininterrotta residua": "",
        "Pausa obbligatoria residua": "",
        "Ultima posizione GPS": ""
    }
    # Esempio parsing. Puoi raffinare con regex a seconda delle immagini
    lines = testo.splitlines()
    for line in lines:
        l = line.lower()
        if "nome" in l or "autista" in l:
            estratti["Nome autista"] = line.split(":")[-1].strip()
        elif "settimana" in l:
            estratti["Inizio settimana"] = line.split(":")[-1].strip()
        elif "guida residua settimanale" in l or "settimanali" in l:
            estratti["Ore guida residue settimana"] = line.split(":")[-1].strip()
        elif "guida residua oggi" in l or "oggi" in l:
            estratti["Ore guida residue oggi"] = line.split(":")[-1].strip()
        elif "ininterrotta" in l:
            estratti["Guida ininterrotta residua"] = line.split(":")[-1].strip()
        elif "pausa" in l:
            estratti["Pausa obbligatoria residua"] = line.split(":")[-1].strip()
        elif "gps" in l or "posizione" in l:
            estratti["Ultima posizione GPS"] = line.split(":")[-1].strip()
    return estratti
import pytesseract
from PIL import Image

def estrai_dati_autista_da_immagine(image_file):
    """Legge i dati autista da una immagine tramite OCR e restituisce un dizionario"""
    img = Image.open(image_file)
    testo = pytesseract.image_to_string(img, lang='ita+eng')
    # SEMPLICE parsing: cerca pattern comuni. Migliorabile con regex!
    estratti = {
        "Nome autista": "",
        "Inizio settimana": "",
        "Ore guida residue settimana": "",
        "Ore guida residue oggi": "",
        "Guida ininterrotta residua": "",
        "Pausa obbligatoria residua": "",
        "Ultima posizione GPS": ""
    }
    # Esempio parsing. Puoi raffinare con regex a seconda delle immagini
    lines = testo.splitlines()
    for line in lines:
        l = line.lower()
        if "nome" in l or "autista" in l:
            estratti["Nome autista"] = line.split(":")[-1].strip()
        elif "settimana" in l:
            estratti["Inizio settimana"] = line.split(":")[-1].strip()
        elif "guida residua settimanale" in l or "settimanali" in l:
            estratti["Ore guida residue settimana"] = line.split(":")[-1].strip()
        elif "guida residua oggi" in l or "oggi" in l:
            estratti["Ore guida residue oggi"] = line.split(":")[-1].strip()
        elif "ininterrotta" in l:
            estratti["Guida ininterrotta residua"] = line.split(":")[-1].strip()
        elif "pausa" in l:
            estratti["Pausa obbligatoria residua"] = line.split(":")[-1].strip()
        elif "gps" in l or "posizione" in l:
            estratti["Ultima posizione GPS"] = line.split(":")[-1].strip()
    return estratti
# --- Dati Autista (Sidebar) ---
st.sidebar.header("Dati Autista")

uploaded_image = st.sidebar.file_uploader("Carica screenshot dati autista (jpg/png)", type=["jpg", "jpeg", "png"])
dati_autista = {}

if uploaded_image:
    with st.spinner("Estrazione dati da immagine..."):
        dati_autista = estrai_dati_autista_da_immagine(uploaded_image)
    st.sidebar.success("Dati autista estratti dall'immagine!")
    # I campi di default sono valorizzati dai dati estratti
else:
    dati_autista = {}

autista_nome = st.sidebar.text_input("Nome autista", dati_autista.get("Nome autista", "S.Pituscan"))
inizio_settimana = st.sidebar.text_input("Inizio settimana lavorativa", dati_autista.get("Inizio settimana", "2025-07-09"))
ora_inizio_sett = st.sidebar.text_input("Ora inizio settimana", "07:00")
ore_guida_sett = st.sidebar.text_input("Ore guida residue settimana", dati_autista.get("Ore guida residue settimana", "56"))
ore_guida_giorno = st.sidebar.text_input("Ore guida residue oggi", dati_autista.get("Ore guida residue oggi", "9"))
tempo_guida_ininterrotta = st.sidebar.text_input("Guida ininterrotta residua (min)", dati_autista.get("Guida ininterrotta residua", "270"))
pausa_necessaria = st.sidebar.text_input("Pausa obbligatoria residua (min)", dati_autista.get("Pausa obbligatoria residua", "45"))
posizione_gps = st.sidebar.text_input("Ultima posizione GPS (lat, lon)", dati_autista.get("Ultima posizione GPS", "45.7636166, 10.9984833"))

st.sidebar.markdown("---")
st.sidebar.write(f"**Autista:** {autista_nome}")
st.sidebar.write(f"Ultima posizione: {posizione_gps}")
st.sidebar.write(f"Inizio settimana: {inizio_settimana} {ora_inizio_sett}")
st.sidebar.write(f"Ore guida residue settimana: {ore_guida_sett}")
st.sidebar.write(f"Ore guida residue oggi: {ore_guida_giorno}")
st.sidebar.write(f"Guida ininterrotta residua: {tempo_guida_ininterrotta} min")
st.sidebar.write(f"Pausa obbligatoria residua: {pausa_necessaria} min")


