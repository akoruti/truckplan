# app_analytics.py
import streamlit as st
import pandas as pd
import altair as alt
import io
from cryptography.fernet import Fernet

# Configurazione pagina
st.set_page_config(page_title="Analytics Viaggi", layout="wide")

# Utility: caricamento dati CSV
@st.cache_data
def load_data(raw_bytes, sep, enc, na_vals):
    sample = io.BytesIO(raw_bytes)
    cols = pd.read_csv(sample, sep=sep, encoding=enc, nrows=0).columns.tolist()
    date_cols = [c for c in ['CPT', 'Data/ora creazione VR (UTC)', 'Data/ora di annullamento VR (UTC)'] if c in cols]
    data_io = io.BytesIO(raw_bytes)
    df = pd.read_csv(
        data_io,
        sep=sep,
        encoding=enc,
        na_values=na_vals,
        parse_dates=date_cols,
        dayfirst=True,
        infer_datetime_format=True,
        low_memory=False
    )
    return df

# Utility: crittografia
@st.cache_data
def encrypt_bytes(data_bytes):
    key = Fernet.generate_key()
    cipher = Fernet(key)
    encrypted = cipher.encrypt(data_bytes)
    return key, encrypted

# Sidebar: upload, opzioni e encrypt
st.sidebar.header("Carica, Filtri e Encrypt")
uploaded = st.sidebar.file_uploader("Seleziona CSV Viaggi", type="csv")
sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
na_input = st.sidebar.text_input("Valori NA (sep. virgola)", "")
na_vals = [v.strip() for v in na_input.split(',') if v.strip()]
encrypt_option = st.sidebar.checkbox("Encrypt file raw")

if not uploaded:
    st.info("Carica un file per continuare")
    st.stop()

# Leggi dati raw e opzionale encryption
raw = uploaded.read()
if encrypt_option:
    key, encrypted = encrypt_bytes(raw)
    st.sidebar.success("File criptato con successo!")
    st.sidebar.code(key.decode(), language='text')
    st.sidebar.download_button("Download Encrypted", encrypted, file_name="encrypted_data.bin")

# Carica DataFrame per analisi
df = load_data(raw, sep, enc, na_vals)

# Filtri dinamici
st.sidebar.subheader("Filtro Stato/Corriere")
stati = df['Stato'].dropna().unique().tolist() if 'Stato' in df else []
corrieri = df['Corriere'].dropna().unique().tolist() if 'Corriere' in df else []
sel_stati = st.sidebar.multiselect("Stato", stati, default=stati)
sel_corrieri = st.sidebar.multiselect("Corriere", corrieri, default=corrieri)

mask = df['Stato'].isin(sel_stati) & df['Corriere'].isin(sel_corrieri)
df_f = df[mask]

# Tabs di analisi delle visualizzazioni
tabs = st.tabs(["Stato Viaggi", "Trend Tempo", "Autisti & Corrieri", "Costi", "Flussi Origine-Dest."])

with tabs[0]:
    st.header("Distribuzione Viaggi per Stato")
    cnt = df_f['Stato'].value_counts().reset_index()
    cnt.columns = ['Stato', 'Conteggio']
    bar = alt.Chart(cnt).mark_bar().encode(
        x='Stato:N', y='Conteggio:Q', color='Stato:N', tooltip=['Stato', 'Conteggio']
    )
    st.altair_chart(bar, use_container_width=True)
    st.dataframe(cnt)

with tabs[1]:
    st.header("Trend Settimanale/Mensile")
    date_col = 'Data/ora creazione VR (UTC)'
    if date_col in df_f.columns:
        df_f['Week'] = df_f[date_col].dt.to_period('W').apply(lambda r: r.start_time)
        df_f['Month'] = df_f[date_col].dt.to_period('M').apply(lambda r: r.start_time)
        for freq, label in [('Week','Settimanale'), ('Month','Mensile')]:
            grp = df_f.groupby(freq)['ID VR'].count().reset_index().rename(columns={'ID VR':'Count'})
            st.subheader(f"Trend {label}")
            line = alt.Chart(grp).mark_line(point=True).encode(
                x=f'{freq}:T', y='Count:Q', tooltip=[freq, 'Count']
            )
            st.altair_chart(line, use_container_width=True)
    else:
        st.warning("Colonna data creazione non disponibile.")

with tabs[2]:
    st.header("Performance Corrieri e Autisti")
    if 'Corriere' in df_f and 'Stato' in df_f:
        met = df_f.groupby(['Corriere', 'Stato'])['ID VR'].count().reset_index()
        chart = alt.Chart(met).mark_bar().encode(
            x='Corriere:N', y='ID VR:Q', color='Stato:N', tooltip=['Corriere','Stato','ID VR']
        )
        st.altair_chart(chart, use_container_width=True)
    if 'Conducente' in df_f:
        drv = df_f['Conducente'].value_counts().reset_index()
        drv.columns = ['Conducente', 'Count']
        st.subheader("Viaggi per Autista")
        bar2 = alt.Chart(drv.head(20)).mark_bar().encode(
            x='Conducente:N', y='Count:Q', tooltip=['Conducente','Count']
        )
        st.altair_chart(bar2, use_container_width=True)

with tabs[3]:
    st.header("Analisi Costi Stimati")
    colc = 'Costo stimato'
    if colc in df_f.columns:
        df_f['Costo_Num'] = pd.to_numeric(df_f[colc], errors='coerce')
        st.subheader("Istogramma Costo Stimato")
        hist = alt.Chart(df_f).mark_bar().encode(
            alt.X('Costo_Num:Q', bin=alt.Bin(maxbins=50)), y='count()', tooltip=['count()']
        )
        st.altair_chart(hist, use_container_width=True)
        st.subheader("Boxplot Costo Stimato")
        box = alt.Chart(df_f).mark_boxplot().encode(y='Costo_Num:Q')
        st.altair_chart(box, use_container_width=True)
    else:
        st.warning("Colonna 'Costo stimato' non trovata.")

with tabs[4]:
    st.header("Origine → Destinazione")
    if 'Sequenza delle strutture' in df_f:
        seq = df_f['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
        df_f['Origine'] = seq[0]; df_f['Destinazione'] = seq[1]
    if 'Origine' in df_f and 'Destinazione' in df_f:
        flow = df_f.groupby(['Origine','Destinazione']).size().reset_index(name='Count')
        st.dataframe(flow.sort_values('Count', ascending=False).head(50))
    else:
        st.warning("Colonne Origine/Destinazione mancanti.")
