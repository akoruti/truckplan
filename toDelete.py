# app.py

import streamlit as st
import pandas as pd
import altair as alt

# Configurazione pagina
st.set_page_config(page_title="Dashboard Analisi Dati", layout="wide")
st.title("Interfaccia Analisi Dati")

# Caricamento file CSV
uploaded_file = st.file_uploader("Carica un file CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # --- Sezione Analisi Generali ---
    st.subheader("🔎 Analisi Generali dei Dati")
    with st.expander("Statistiche Descrittive"):  
        st.write(df.describe(include='all').T)
    with st.expander("Valori Mancanti"):  
        missing = df.isnull().sum()
        st.write(missing[missing > 0])
    
    # --- Sidebar: Scelta tipo di analisi ---
    st.sidebar.header("Seleziona Analisi")
    analysis = st.sidebar.selectbox("Tipo di Analisi", [
        "Panoramica Colonne", "Istogramma", "Scatter Plot", "Correlazioni"
    ])
    
    # Panoramica Colonne
    if analysis == "Panoramica Colonne":
        st.subheader("📋 Panoramica Colonne")
        overview = pd.DataFrame({
            'Tipo Dato': df.dtypes.astype(str),
            'Unique': df.nunique(),
            'Missing': df.isnull().sum(),
            'Non Missing': df.notnull().sum()
        })
        st.dataframe(overview)
        
    # Istogramma
    elif analysis == "Istogramma":
        st.subheader("📊 Istogramma")
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        if not numeric_cols:
            st.warning("Nessuna colonna numerica disponibile.")
        else:
            col = st.sidebar.selectbox("Colonna Numerica", numeric_cols)
            bins = st.sidebar.slider("Numero di bin", 5, 100, 20)
            chart = alt.Chart(df).mark_bar().encode(
                alt.X(col, bin=alt.Bin(maxbins=bins)),
                y='count()'
            )
            st.altair_chart(chart, use_container_width=True)
    
    # Scatter Plot
    elif analysis == "Scatter Plot":
        st.subheader("🔵 Scatter Plot")
        numeric = df.select_dtypes(include=['number']).columns.tolist()
        if len(numeric) < 2:
            st.warning("Serve almeno 2 colonne numeriche.")
        else:
            x_axis = st.sidebar.selectbox("Asse X", numeric)
            y_axis = st.sidebar.selectbox("Asse Y", numeric, index=1)
            chart = alt.Chart(df).mark_circle(size=60).encode(
                x=alt.X(x_axis, type='quantitative'),
                y=alt.Y(y_axis, type='quantitative'),
                tooltip=numeric
            )
            st.altair_chart(chart, use_container_width=True)
    
    # Correlazioni
    else:
        st.subheader("📈 Matrice di Correlazione")
        corr = df.select_dtypes(include=['number']).corr()
        st.write(corr)

else:
    st.info("Attendi il caricamento di un file CSV per avviare l'analisi.")

# Esecuzione:
# 1. pip install streamlit pandas altair
# 2. streamlit run app.py




