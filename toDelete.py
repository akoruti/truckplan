import streamlit as st
import pandas as pd
import altair as alt
import io

# Configurazione pagina
st.set_page_config(page_title="Analytics Viaggi", layout="wide")

@st.cache_data
def load_data(raw_bytes, sep, enc, na_vals):
    """
    Carica un CSV da raw bytes con opzioni di separatore, encoding e valori NA.
    Restituisce un DataFrame pandas.
    """
    sample = io.BytesIO(raw_bytes)
    try:
        cols = pd.read_csv(sample, sep=sep, encoding=enc, nrows=0).columns.tolist()
    except Exception:
        cols = []
    date_cols = [c for c in cols if c in [
        'CPT', 'Data/ora creazione VR (UTC)', 'Data/ora di annullamento VR (UTC)'
    ]]
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


def main():
    # Sidebar: upload e opzioni di parsing
    st.sidebar.header("Carica e Filtra CSV")
    uploaded = st.sidebar.file_uploader("Seleziona CSV Viaggi", type=["csv"])
    sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
    enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
    na_input = st.sidebar.text_input("Valori NA (separati da virgola)", "")
    na_vals = [v.strip() for v in na_input.split(',') if v.strip()]

    if not uploaded:
        st.info("Carica un file CSV per proseguire.")
        st.stop()

    raw_bytes = uploaded.read()
    df = load_data(raw_bytes, sep, enc, na_vals)

    # Filtri dinamici
    df_filtered = df.copy()
    if 'Stato' in df.columns:
        state_opts = df['Stato'].dropna().unique().tolist()
        selected_states = st.sidebar.multiselect("Stato", state_opts, default=state_opts)
        df_filtered = df_filtered[df_filtered['Stato'].isin(selected_states)]
    else:
        st.sidebar.warning("Colonna 'Stato' non trovata.")

    if 'Corriere' in df.columns:
        carrier_opts = df['Corriere'].dropna().unique().tolist()
        selected_carriers = st.sidebar.multiselect("Corriere", carrier_opts, default=carrier_opts)
        df_filtered = df_filtered[df_filtered['Corriere'].isin(selected_carriers)]
    else:
        st.sidebar.warning("Colonna 'Corriere' non trovata.")

    # Definizione tabs
    tabs = st.tabs([
        "Stato Viaggi",
        "Trend Tempo",
        "Autisti & Corrieri",
        "Costi Stimati",
        "Flussi Orig-Dest"
    ])

    # 1. Stato Viaggi
    with tabs[0]:
        st.header("Distribuzione Viaggi per Stato")
        if 'Stato' in df_filtered.columns:
            cnt = df_filtered['Stato'].value_counts().reset_index()
            cnt.columns = ['Stato', 'Conteggio']
            chart = alt.Chart(cnt).mark_bar().encode(
                x='Stato:N', y='Conteggio:Q', color='Stato:N', tooltip=['Stato','Conteggio']
            )
            st.altair_chart(chart, use_container_width=True)
            st.dataframe(cnt)
        else:
            st.warning("Nessuna colonna 'Stato' disponibile.")

    # 2. Trend Settimanale/Mensile
    with tabs[1]:
        st.header("Trend Settimanale e Mensile")
        date_col = 'Data/ora creazione VR (UTC)'
        if date_col in df_filtered.columns:
            df_filtered['Week'] = df_filtered[date_col].dt.to_period('W').apply(lambda r: r.start_time)
            df_filtered['Month'] = df_filtered[date_col].dt.to_period('M').apply(lambda r: r.start_time)
            for freq, label in [('Week','Settimanale'), ('Month','Mensile')]:
                grp = df_filtered.groupby(freq)['ID VR'].count().reset_index().rename(columns={'ID VR':'Count'})
                st.subheader(f"Trend {label}")
                line = alt.Chart(grp).mark_line(point=True).encode(
                    x=f'{freq}:T', y='Count:Q', tooltip=[freq,'Count']
                )
                st.altair_chart(line, use_container_width=True)
        else:
            st.warning(f"Colonna '{date_col}' non disponibile.")

    # 3. Performance Corrieri e Autisti
    with tabs[2]:
        st.header("Performance Corrieri e Autisti")
        if {'Corriere','Stato','ID VR'}.issubset(df_filtered.columns):
            met = df_filtered.groupby(['Corriere','Stato'])['ID VR'].count().reset_index()
            chart = alt.Chart(met).mark_bar().encode(
                x='Corriere:N', y='ID VR:Q', color='Stato:N', tooltip=['Corriere','Stato','ID VR']
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning("Colonne per analisi Corriere/Stato non disponibili.")
        if 'Conducente' in df_filtered.columns:
            drv = df_filtered['Conducente'].value_counts().reset_index()
            drv.columns = ['Conducente','Count']
            st.subheader("Viaggi per Autista (Top 20)")
            bar2 = alt.Chart(drv.head(20)).mark_bar().encode(
                x='Conducente:N', y='Count:Q', tooltip=['Conducente','Count']
            )
            st.altair_chart(bar2, use_container_width=True)
        else:
            st.warning("Colonna 'Conducente' non disponibile.")

    # 4. Analisi Costi Stimati
    with tabs[3]:
        st.header("Analisi Costi Stimati")
        cost_col = 'Costo stimato'
        if cost_col in df_filtered.columns:
            def parse_euro(x):
                try:
                    s = str(x).replace('€','').replace(' ','')
                    if '.' in s and ',' in s:
                        s = s.replace('.','').replace(',','.')
                    else:
                        s = s.replace(',','.')
                    return float(s)
                except:
                    return None
            df_filtered['Costo_Num'] = df_filtered[cost_col].apply(parse_euro)
            st.subheader("Istogramma Costo Stimato")
            hist = alt.Chart(df_filtered).mark_bar().encode(
                alt.X('Costo_Num:Q', bin=alt.Bin(maxbins=50)), y='count()', tooltip=['count()']
            )
            st.altair_chart(hist, use_container_width=True)
            st.subheader("Boxplot Costo Stimato")
            box = alt.Chart(df_filtered).mark_boxplot().encode(y='Costo_Num:Q')
            st.altair_chart(box, use_container_width=True)
            nums = df_filtered.select_dtypes(include=['number'])
            corr = nums.corr().stack().reset_index().rename(columns={'level_0':'x','level_1':'y',0:'corr'})
            heat = alt.Chart(corr).mark_rect().encode(
                x='x:N', y='y:N', color='corr:Q', tooltip=['x','y','corr']
            )
            st.subheader("Matrice di Correlazione")
            st.altair_chart(heat, use_container_width=True)
        else:
            st.warning(f"Colonna '{cost_col}' non disponibile.")

    # 5. Flussi Origine → Destinazione
    with tabs[4]:
        st.header("Origine → Destinazione")
        if 'Sequenza delle strutture' in df_filtered.columns:
            seq = df_filtered['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
            df_filtered['Origine'], df_filtered['Destinazione'] = seq[0], seq[1]
        if {'Origine','Destinazione'}.issubset(df_filtered.columns):
            flow = df_filtered.groupby(['Origine','Destinazione']).size().reset_index(name='Count')
            st.dataframe(flow.sort_values('Count', ascending=False).head(50))
        else:
            st.warning("Colonne Origine/Destinazione non disponibili.")

if __name__ == '__main__':
    main()
