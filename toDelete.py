# app.py
import streamlit as st
import pandas as pd
import altair as alt
import io

@st.cache_data
def load_csv(data, sep, enc, na_values):
    try:
        df = pd.read_csv(
            io.BytesIO(data),
            sep=sep,
            encoding=enc,
            na_values=na_values,
            parse_dates=True,
            dayfirst=True,
            infer_datetime_format=True,
            low_memory=False
        )
        return df, None
    except Exception as e:
        return None, str(e)


def main():
    st.set_page_config(page_title="Dashboard Viaggi e Compensi", layout="wide")
    st.title("Dashboard Viaggi e Compensi per Autista")

    # Sidebar: CSV options + filters + pagination
    st.sidebar.header("Caricamento e Filtri")
    uploaded = st.sidebar.file_uploader("File CSV", type="csv")
    sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
    enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
    na_list = [v.strip() for v in st.sidebar.text_input("Valori NaN (sep. virgola)", "").split(",") if v.strip()]
    
    if not uploaded:
        st.info("Carica un file CSV per iniziare")
        return

    df, error = load_csv(uploaded.read(), sep, enc, na_list)
    if error:
        st.error(f"Errore lettura CSV: {error}")
        return

    # Preprocessing
    if 'Sequenza delle strutture' in df.columns:
        seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
        df['Origine'], df['Destinazione'] = seq[0], seq[1]
    if 'ID Veicolo' in df.columns:
        df['Targa'] = df['ID Veicolo'].astype(str).str.extract(r'OTHR-(.*)')
    if 'Costo stimato' in df.columns:
        df['Costo_Num'] = pd.to_numeric(df['Costo stimato'], errors='coerce')
    else:
        df['Costo_Num'] = pd.NA

    # Filters
    states = df['Stato'].unique().tolist() if 'Stato' in df.columns else []
    carriers = df['Corriere'].unique().tolist() if 'Corriere' in df.columns else []
    selected_states = st.sidebar.multiselect("Stato", states, default=states)
    selected_carriers = st.sidebar.multiselect("Corriere", carriers, default=carriers)
    filtered = df[df['Stato'].isin(selected_states) & df['Corriere'].isin(selected_carriers)]

    # Pagination controls
    st.sidebar.header("Tabella Viaggi")
    rows_per_page = st.sidebar.number_input("Righe per pagina", min_value=5, max_value=100, value=20)
    total_rows = filtered.shape[0]
    total_pages = (total_rows - 1) // rows_per_page + 1
    page = st.sidebar.number_input("Pagina", min_value=1, max_value=total_pages, value=1)

    # Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totale Viaggi", total_rows)
    with col2:
        avg_cost = filtered['Costo_Num'].mean()
        st.metric("Compenso Medio (€)", f"{avg_cost:.2f}")
    with col3:
        tot_cost = filtered['Costo_Num'].sum()
        st.metric("Compenso Totale (€)", f"{tot_cost:.2f}")

    # Detailed table with pagination
    st.subheader("Dettagli Viaggi")
    start = (page - 1) * rows_per_page
    end = start + rows_per_page
    display_cols = ['ID VR', 'Stato', 'Corriere', 'Conducente', 'Origine', 'Destinazione', 'Targa', 'Costo_Num']
    display_cols = [c for c in display_cols if c in filtered.columns]
    st.dataframe(filtered[display_cols].iloc[start:end].reset_index(drop=True))
    st.write(f"Mostrati {start+1}–{min(end, total_rows)} di {total_rows} viaggi")

    # Charts
    st.subheader("Distribuzione Viaggi per Stato")
    counts = filtered['Stato'].value_counts().reset_index()
    counts.columns = ['Stato', 'Conteggio']
    bar = alt.Chart(counts).mark_bar().encode(
        x=alt.X('Stato:N', sort=states),
        y='Conteggio:Q',
        color='Stato:N',
        tooltip=['Stato', 'Conteggio']
    )
    st.altair_chart(bar, use_container_width=True)

    st.subheader("Percentuale Camion CPT")
    if 'È un camion CPT' in filtered.columns:
        pie_data = filtered['È un camion CPT'].value_counts(normalize=True).rename(index={True:'Camion', False:'Non Camion'}).reset_index()
        pie_data.columns = ['Categoria', 'Percentuale']
        pie = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
            theta='Percentuale:Q',
            color='Categoria:N',
            tooltip=['Categoria', alt.Tooltip('Percentuale:Q', format='.2%')]
        )
        st.altair_chart(pie, use_container_width=True)

    # Compensation by driver
    if 'Conducente' in filtered.columns:
        st.subheader("Compenso per Autista")
        stats = (filtered.groupby('Conducente')['Costo_Num']
                 .agg(Totale='sum', Media='mean', Viaggi='count')
                 .reset_index().sort_values('Totale', ascending=False))
        top_n = st.sidebar.slider("Top N autisti", 3, min(20, stats.shape[0]), 10)
        top = stats.head(top_n)
        st.dataframe(top)
        bar_tot = alt.Chart(top).mark_bar().encode(
            x=alt.X('Conducente:N', sort='-y'),
            y='Totale:Q',
            tooltip=['Conducente', alt.Tooltip('Totale:Q', title='Totale (€)'), 'Media', 'Viaggi']
        )
        st.altair_chart(bar_tot, use_container_width=True)

if __name__ == '__main__':
    main()
