
import streamlit as st
import pandas as pd
import numpy as np

# --- Config ---
st.set_page_config(page_title="Programmazione Viaggi", layout="wide")

st.title("Programmazione Viaggi Autista")
st.markdown("Tutte le regole di layout, riga totale, costi, selezione sono applicate automaticamente.")

# --- Carica dati ---
st.subheader("1. Carica i viaggi disponibili")
uploaded_file = st.file_uploader("Carica file CSV o Excel", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith('.csv'):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
else:
    # Esempio dati demo se non carichi file
   # --- Dati Autista ---
st.sidebar.header("Dati Autista")
autista_nome = st.sidebar.text_input("Nome autista", "S.Pituscan")
inizio_settimana = st.sidebar.date_input("Inizio settimana lavorativa", pd.to_datetime("2025-07-09"))
ora_inizio = st.sidebar.time_input("Ora inizio giornata", pd.to_datetime("07:00").time())
ore_guida_sett = st.sidebar.number_input("Ore guida residue settimana", 0.0, 56.0, 56.0, step=0.25)
ore_guida_giorno = st.sidebar.number_input("Ore guida residue oggi", 0.0, 9.0, 9.0, step=0.25)
tempo_guida_ininterrotta = st.sidebar.number_input("Tempo guida ininterrotta (min)", 0, 270, 270, step=5)
pausa_necessaria = st.sidebar.number_input("Minuti pausa obbligatoria", 0, 45, 45, step=5)
st.sidebar.write("---")
st.sidebar.write(f"**Autista selezionato:** {autista_nome}")

# Puoi salvare questi dati in session_state o usarli per filtri/calcoli sulle ore disponibili!
 df = pd.DataFrame([
        {"Codice Viaggio":"115C6227S", "Partenza":"NUE9 Eggolsheim", "Data/Ora Partenza":"gio, 10 lug, 08:30 CEST", "Destinazione":"LIN8 Casirate D'Adda", "Data/Ora Arrivo":"ven, 11 lug, 14:15 CEST", "Distanza":728, "Durata stimata":"1g 7h", "Compenso (€)":1508.46, "€/km":2.07, "Rimorchio":"sganciato", "Modalità":"In tempo reale"},
        {"Codice Viaggio":"115K75KXK", "Partenza":"LIN8 Casirate D’Adda", "Data/Ora Partenza":"ven, 11 lug, 19:00", "Destinazione":"BLQ1 San Bellino, Rovigo", "Data/Ora Arrivo":"ven, 11 lug, 23:00", "Distanza":192.2, "Durata stimata":"5h 0m", "Compenso (€)":490.28, "€/km":2.55, "Rimorchio":"sganciato", "Modalità":"In tempo reale"},
        {"Codice Viaggio":"da inserire", "Partenza":"BLQ1 SAN BELLINO", "Data/Ora Partenza":"sab, 12 lug, 14:00", "Destinazione":"DMR1 CAMERANO", "Data/Ora Arrivo":"sab, 12 lug, 21:27", "Distanza":294.5, "Durata stimata":"7h 27m", "Compenso (€)":891.61, "€/km":3.03, "Rimorchio":"Semi-rimorchio", "Modalità":"In tempo reale"}
    ])

# --- Parametri costi ---
st.sidebar.header("Parametri costi")
prezzo_gasolio = st.sidebar.number_input("Prezzo gasolio €/l", 1.2, 3.0, 1.69, step=0.01)
consumo_km_l = st.sidebar.number_input("Consumo medio (km/l)", 2.0, 6.0, 3.5, step=0.1)
st.sidebar.markdown("*I pedaggi sono stimati manualmente, aggiorna i valori nella tabella se hai dati precisi.*")

# --- Calcolo costi carburante e pedaggi ---
def stima_carburante(distanza, km_l, prezzo):
    try:
        return round((float(distanza) / km_l) * prezzo, 2)
    except:
        return 0

if "Carburante (€)" not in df.columns:
    df["Carburante (€)"] = df["Distanza"].apply(lambda x: stima_carburante(x, consumo_km_l, prezzo_gasolio))

if "Pedaggi (€)" not in df.columns:
    # Stima di default. Puoi aggiornare manualmente.
    pedaggi_default = [78, 22, 54][:len(df)]
    df["Pedaggi (€)"] = pedaggi_default + [0]*(len(df)-len(pedaggi_default))

df["Totale costi (€)"] = df["Carburante (€)"] + df["Pedaggi (€)"]

# --- Tabella modificabile ---
st.subheader("2. Tabella programmazione (modificabile, seleziona per copiare)")
edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

# --- Riga totale ---
totale_row = {
    "Codice Viaggio": "TOTALE",
    "Partenza": "",
    "Data/Ora Partenza": "",
    "Destinazione": "",
    "Data/Ora Arrivo": "",
    "Distanza": edited_df["Distanza"].sum(),
    "Durata stimata": "",
    "Compenso (€)": edited_df["Compenso (€)"].sum(),
    "€/km": round(edited_df["Compenso (€)"].sum()/edited_df["Distanza"].sum(), 2) if edited_df["Distanza"].sum() else "",
    "Rimorchio": "",
    "Modalità": "",
    "Carburante (€)": edited_df["Carburante (€)"].sum(),
    "Pedaggi (€)": edited_df["Pedaggi (€)"].sum(),
    "Totale costi (€)": edited_df["Totale costi (€)"].sum(),
}
tot_df = pd.concat([edited_df, pd.DataFrame([totale_row])], ignore_index=True)

st.dataframe(tot_df, use_container_width=True)

# --- Esporta CSV ---
st.download_button("Scarica CSV", data=tot_df.to_csv(index=False), file_name="programmazione_viaggi.csv")

# --- Extra: Analisi automatica ---
with st.expander("Suggerisci programmazione ottimale"):
    st.write("Prossimamente: modulo AI/autonomo per suggerire la miglior sequenza viaggi secondo compenso, vincoli, orari e costi!")

# --- Fine prototipo ---

st.success("Regole e struttura personalizzate come richiesto. Puoi integrare moduli OCR/API Amazon in ogni momento!")

