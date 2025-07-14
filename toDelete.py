import streamlit as st
import pandas as pd
import altair as alt
import io

@st.cache_data
def load_csv(data, sep, enc, na_values):
    """
    Carica un CSV da bytes con opzioni di separatore, encoding e valori NA.
    Restituisce DataFrame o errore.
    """
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


def trova_colonna_costo(df):
    """
    Trova la colonna contenente sia 'costo' che 'stimato' (case-insensitive).
    """
    for col in df.columns:
        nome = col.lower().replace(" ", "")
        if "costo" in nome and "stimato" in nome:
            return col
    return None


def main():
    st.set_page_config(page_title="Dashboard Viaggi e Compensi", layout="wide")
    st.title("Dashboard Viaggi e Compensi per Autista")

    # Sidebar: caricamento file e opzioni
    st.sidebar.header("Caricamento e Filtri CSV")
    uploaded = st.sidebar.file_uploader("Seleziona file CSV", type="csv")
    sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
    enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
    na_input = st.sidebar.text_input("Valori NaN (separati da virgola)", "")
    na_list = [v.strip() for v in na_input.split(",") if v.strip()]

    if not uploaded:
        st.info("Carica un file CSV per iniziare.")
        return

    data = uploaded.read()
    df, error = load_csv(data, sep, enc, na_list)
    if error:
        st.error(f"Errore lettura CSV: {error}")
        return

    # Estrazioni iniziali
    if 'Sequenza delle strutture' in df.columns:
        seq = df['Sequenza delle strutture'].astype(str).str.split('->', expand=True)
        df['Origine'] = seq[0]
        df['Destinazione'] = seq[1]
    if 'ID Veicolo' in df.columns:
        df['Targa'] = df['ID Veicolo'].astype(str).str.extract(r'OTHR-(.*)')

    # Colonna costo dinamica
    col_costo = trova_colonna_costo(df)
    if col_costo:
        df['Costo_Num'] = pd.to_numeric(df[col_costo], errors='coerce')
    else:
        df['Costo_Num'] = pd.NA
        st.warning("Colonna compenso non trovata, Costo_Num impostata a NaN.")

    # Filtri dinamici
    st.sidebar.header("Filtri Viaggi")
    stati = list(df['Stato'].unique()) if 'Stato' in df.columns else []
    corrieri = list(df['Corriere'].unique()) if 'Corriere' in df.columns else []
    sel_stati = st.sidebar.multiselect("Stato", stati, default=stati)
    sel_corrieri = st.sidebar.multiselect("Corriere", corrieri, default=corrieri)
    filtered = df[df['Stato'].isin(sel_stati) & df['Corriere'].isin(sel_corrieri)]

    # Metriche principali
    total_viaggi = len(filtered)
    avg_cost = filtered['Costo_Num'].mean(skipna=True)
    total_cost = filtered['Costo_Num'].sum(skipna=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Totale Viaggi", total_viaggi)
    c2.metric("Compenso Medio (€)", f"{avg_cost:.2f}")
    c3.metric("Compenso Totale (€)", f"{total_cost:.2f}")

    # Tabella dettagliata
    st.subheader("Dettagli Viaggi")
    cols = ['ID VR', 'Stato', 'Corriere', 'Conducente', 'Origine', 'Destinazione', 'Targa', 'Costo_Num']
    display_cols = [c for c in cols if c in filtered.columns]
    st.dataframe(filtered[display_cols].reset_index(drop=True))

    # Grafico distribuzione per stato
    if 'Stato' in filtered.columns:
        st.subheader("Distribuzione Viaggi per Stato")
        counts = filtered['Stato'].value_counts().reset_index()
        counts.columns = ['Stato', 'Conteggio']
        chart = alt.Chart(counts).mark_bar().encode(
            x=alt.X('Stato:N', sort='-y'),
            y='Conteggio:Q',
            color='Stato:N',
            tooltip=['Stato', 'Conteggio']
        )
        st.altair_chart(chart, use_container_width=True)

    # Grafico percentuale camion CPT
    if 'È un camion CPT' in filtered.columns:
        st.subheader("Percentuale Camion CPT")
        pie_data = (
            filtered['È un camion CPT']
            .value_counts(normalize=True)
            .rename(index={True: 'Camion', False: 'Non Camion'})
            .reset_index()
        )
        pie_data.columns = ['Categoria', 'Percentuale']
        pie_chart = alt.Chart(pie_data).mark_arc(innerRadius=50).encode(
            theta='Percentuale:Q',
            color='Categoria:N',
            tooltip=[
                alt.Tooltip('Categoria:N', title='Categoria'),
                alt.Tooltip('Percentuale:Q', title='Percentuale', format='.2%')
            ]
        )
        st.altair_chart(pie_chart, use_container_width=True)

    # Analisi compenso per autista
    if 'Conducente' in filtered.columns:
        st.subheader("Compenso per Autista")
        driver_stats = (
            filtered.groupby('Conducente')['Costo_Num']
            .agg(Totale='sum', Media='mean', Viaggi='count')
            .reset_index()
            .sort_values('Totale', ascending=False)
        )
        top_n = st.sidebar.slider("Top N Autisti", min_value=3, max_value=min(20, len(driver_stats)), value=10)
        top = driver_stats.head(top_n)
        st.dataframe(top)
        bar = alt.Chart(top).mark_bar().encode(
            x=alt.X('Conducente:N', sort='-y'),
            y='Totale:Q',
            tooltip=[
                alt.Tooltip('Conducente:N', title='Autista'),
                alt.Tooltip('Totale:Q', title='Totale (€)'),
                alt.Tooltip('Media:Q', title='Media (€)'),
                alt.Tooltip('Viaggi:Q', title='Viaggi')
            ]
        )
        st.altair_chart(bar, use_container_width=True)

if __name__ == '__main__':
    main()

