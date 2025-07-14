# app_analytics.py
import streamlit as st
import pandas as pd
import altair as alt
import io

st.set_page_config(page_title="Analytics Viaggi", layout="wide")

@st.cache_data
def load_data(raw_bytes, sep, enc, na_vals):
    """
    Carica un CSV da raw bytes con opzioni di separatore, encoding e valori NA.
    """
    # Usa gli stessi bytes per inferenza e parsing
    # Prima inferisce le date esistenti
    sample = io.BytesIO(raw_bytes)
    cols = pd.read_csv(sample, sep=sep, encoding=enc, nrows=0).columns.tolist()
    date_cols = [c for c in ['CPT', 'Data/ora creazione VR (UTC)', 'Data/ora di annullamento VR (UTC)'] if c in cols]
    # Parsing completo
    data = io.BytesIO(raw_bytes)
    df = pd.read_csv(
        data,
        sep=sep,
        encoding=enc,
        na_values=na_vals,
        parse_dates=date_cols,
        dayfirst=True,
        infer_datetime_format=True,
        low_memory=False
    )
    return df

# Sidebar: upload & options
st.sidebar.header("Carica e Filtra")
uploaded = st.sidebar.file_uploader("Seleziona CSV Viaggi", type="csv")
sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
na_input = st.sidebar.text_input("Valori NA (sep. virgola)", "")
na_vals = [v.strip() for v in na_input.split(',') if v.strip()]

if not uploaded:
    st.info("Carica un file per continuare")
    st.stop()

# Leggi dati
raw = uploaded.read()
df = load_data(raw, sep, enc, na_vals)

# Basic filters
st.sidebar.subheader("Filtro Stato/Corriere")
stati = df['Stato'].dropna().unique().tolist()
corrieri = df['Corriere'].dropna().unique().tolist()
sel_stati = st.sidebar.multiselect("Stato", stati, default=stati)
sel_corrieri = st.sidebar.multiselect("Corriere", corrieri, default=corrieri)

mask = df['Stato'].isin(sel_stati) & df['Corriere'].isin(sel_corrieri)
df_f = df[mask]

# Tabs
tabs = st.tabs(["Stato Viaggi", "Trend Tempo", "Autisti & Corrieri", "Costi", "Flussi Origine-Dest."])

# 1. Stato Viaggi
with tabs[0]:
    st.header("Distribuzione Viaggi per Stato")
    cnt = df_f['Stato'].value_counts().reset_index()
    cnt.columns = ['Stato','Conteggio']
    chart = alt.Chart(cnt).mark_bar().encode(
        x=alt.X('Stato:N'), y='Conteggio:Q', color='Stato:N', tooltip=['Stato','Conteggio']
    )
    st.altair_chart(chart, use_container_width=True)
    st.dataframe(cnt)

# 2. Trend Tempo
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
                x=f'{freq}:T', y='Count:Q', tooltip=[freq,'Count']
            )
            st.altair_chart(line, use_container_width=True)
    else:
        st.warning("Colonna data creazione non disponibile.")

# 3. Autisti & Corrieri
with tabs[2]:
    st.header("Performance Corrieri e Autisti")
    metric = df_f.groupby(['Corriere','Stato'])['ID VR'].count().reset_index()
    chart = alt.Chart(metric).mark_bar().encode(
        x='Corriere:N', y='ID VR:Q', color='Stato:N', tooltip=['Corriere','Stato','ID VR']
    )
    st.subheader("Viaggi per Corriere e Stato")
    st.altair_chart(chart, use_container_width=True)
    if 'Conducente' in df_f.columns:
        aut = df_f['Conducente'].value_counts().reset_index()
        aut.columns = ['Conducente','Count']
        st.subheader("Numero Viaggi per Autista")
        bar = alt.Chart(aut.head(20)).mark_bar().encode(
            x='Conducente:N', y='Count:Q', tooltip=['Conducente','Count']
        )
        st.altair_chart(bar, use_container_width=True)

# 4. Costi
with tabs[3]:
    st.header("Analisi Costi Stimati")
    colc = 'Costo stimato'
    if colc in df_f.columns:
        df_f['Costo_Num'] = pd.to_numeric(df_f[colc], errors='coerce')
        st.subheader("Distribuzione Costo Stimato")
        hist = alt.Chart(df_f).mark_bar().encode(
            alt.X('Costo_Num:Q', bin=alt.Bin(maxbins=50)), y='count()', tooltip=['count()']
        )
        st.altair_chart(hist, use_container_width=True)
        st.subheader("Boxplot Costo Stimato")
        box = alt.Chart(df_f).mark_boxplot().encode(y='Costo_Num:Q')
        st.altair_chart(box, use_container_width=True)
        nums = df_f.select_dtypes(include=['number'])
        corr = nums.corr().stack().reset_index().rename(columns={'level_0':'x','level_1':'y',0:'corr'})
        heat = alt.Chart(corr).mark_rect().encode(
            x='x:N', y='y:N', color='corr:Q', tooltip=['x','y','corr']
        )
        st.subheader("Matrice di Correlazione")
        st.altair_chart(heat, use_container_width=True)
    else:
        st.warning("Colonna Costo stimato non trovata.")

# 5. Flussi Origine-Destinazione
with tabs[4]:
    st.header("Frequenza Origine → Destinazione")
    if 'Origine' in df_f.columns and 'Destinazione' in df_f.columns:
        flow = df_f.groupby(['Origine','Destinazione']).size().reset_index(name='Count')
        st.dataframe(flow.sort_values('Count', ascending=False).head(50))
        st.info("Per flussi avanzati si può integrare plotly sankey o altair sankey plugin.")
    else:
        st.warning("Colonne Origine/Destinazione mancanti.")
