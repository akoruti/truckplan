import streamlit as st
import pandas as pd
import altair as alt
import io

# Custom CSS for styling
st.markdown(
    """
    <style>
    .stApp { background-color: #f7f9fc; }
    .streamlit-expanderHeader { font-size:1.2rem; font-weight:bold; color:#1f77b4; }
    .stMetric { background:#fff; border-radius:8px; box-shadow:0 2px 4px rgba(0,0,0,0.1); padding:1rem; margin:0.5rem; }
    .css-1d391kg .css-1lcbmhc h2 { color:#1f77b4; }
    </style>
    """,
    unsafe_allow_html=True
)

PALETTE = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
st.set_page_config(page_title="Analytics Viaggi", layout="wide")

@st.cache_data
def load_data(raw_bytes, sep, enc, na_vals):
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
    # Sidebar: upload and parsing options
    st.sidebar.header("Carica e Filtra CSV")
    uploaded = st.sidebar.file_uploader("Seleziona CSV Viaggi", type=["csv"])
    sep = st.sidebar.selectbox("Delimitatore", [",", ";", "\t"], index=0)
    enc = st.sidebar.selectbox("Encoding", ["utf-8", "latin-1", "utf-16"], index=0)
    na_input = st.sidebar.text_input("Valori NA (separati da virgola)", "")
    na_vals = [v.strip() for v in na_input.split(',') if v.strip()]

    if not uploaded:
        st.info("Carica un file CSV per proseguire.")
        return

    raw_bytes = uploaded.read()
    df = load_data(raw_bytes, sep, enc, na_vals)

    # Filters
    df_filtered = df.copy()
    if 'Stato' in df.columns:
        opts = df['Stato'].dropna().unique().tolist()
        sel = st.sidebar.multiselect("Stato", opts, default=opts)
        df_filtered = df_filtered[df_filtered['Stato'].isin(sel)]
    if 'Corriere' in df.columns:
        opts = df['Corriere'].dropna().unique().tolist()
        sel = st.sidebar.multiselect("Corriere", opts, default=opts)
        df_filtered = df_filtered[df_filtered['Corriere'].isin(sel)]

    # Pre-parse costs
    cost_col = 'Costo stimato'
    def parse_euro(x):
        try:
            s = str(x).replace('€','').replace(' ','').strip()
            if '.' in s and ',' in s:
                s = s.replace('.','').replace(',','.')
            else:
                s = s.replace(',','.')
            return float(s)
        except:
            return None
    if cost_col in df_filtered.columns:
        df_filtered['Costo_Num'] = df_filtered[cost_col].apply(parse_euro)

    # Tabs setup
    tabs = st.tabs(["Stato Viaggi", "Trend Tempo", "Autisti & Corrieri", "Costi Stimati", "Flussi Orig-Dest"])

    with tabs[0]:  # Stato Viaggi
        st.header("🎯 Distribuzione Viaggi per Stato")
        if 'Stato' in df_filtered:
            cnt = df_filtered['Stato'].value_counts().reset_index()
            cnt.columns = ['Stato','Conteggio']
            chart = alt.Chart(cnt).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                x='Stato:N', y='Conteggio:Q', color=alt.Color('Stato:N', scale=alt.Scale(range=PALETTE)), tooltip=['Stato','Conteggio']
            ).properties(height=300)
            st.altair_chart(chart)
            st.dataframe(cnt)

    with tabs[1]:  # Trend Tempo
        st.header("⏳ Trend Settimanale e Mensile")
        dc = 'Data/ora creazione VR (UTC)'
        if dc in df_filtered:
            df_filtered['Week'] = df_filtered[dc].dt.to_period('W').apply(lambda r: r.start_time)
            df_filtered['Month'] = df_filtered[dc].dt.to_period('M').apply(lambda r: r.start_time)
            for freq,label in [('Week','Settimanale'),('Month','Mensile')]:
                grp = df_filtered.groupby(freq)['ID VR'].count().reset_index().rename(columns={'ID VR':'Count'})
                st.subheader(f"Trend {label}")
                line = alt.Chart(grp).mark_line(point=True).encode(
                    x=f'{freq}:T', y='Count:Q', tooltip=[freq,'Count']
                ).properties(height=250)
                st.altair_chart(line)

    with tabs[2]:  # Autisti & Corrieri
        st.header("🚚 Performance Corrieri e Autisti")
        if {'Corriere','Stato','ID VR'}.issubset(df_filtered.columns):
            met = df_filtered.groupby(['Corriere','Stato'])['ID VR'].count().reset_index()
            chart = alt.Chart(met).mark_bar().encode(
                x='Corriere:N', y='ID VR:Q', color=alt.Color('Stato:N', scale=alt.Scale(range=PALETTE)), tooltip=['Corriere','Stato','ID VR']
            ).properties(height=300)
            st.altair_chart(chart)
        if 'Conducente' in df_filtered:
            drv = df_filtered['Conducente'].value_counts().reset_index()
            drv.columns=['Conducente','Count']
            st.subheader("Top 20 Autisti")
            bar = alt.Chart(drv.head(20)).mark_bar().encode(
                x='Conducente:N', y='Count:Q', tooltip=['Conducente','Count']
            ).properties(height=300)
            st.altair_chart(bar)

    with tabs[3]:  # Costi Stimati
        st.header("💰 Analisi Costi Stimati")
        if 'Costo_Num' in df_filtered:
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("Istogramma")
                hist = alt.Chart(df_filtered).mark_bar(color='#2ca02c').encode(
                    alt.X('Costo_Num:Q', bin=alt.Bin(maxbins=50), title='Costo (€)'), y='count()', tooltip=['count()']
                ).properties(height=250)
                st.altair_chart(hist)
            with c2:
                st.subheader("Boxplot")
                box = alt.Chart(df_filtered).mark_boxplot(color='#d62728').encode(
                    y='Costo_Num:Q'
                ).properties(height=250)
                st.altair_chart(box)
            st.subheader("Correlazioni")
            nums = df_filtered.select_dtypes(include='number')
            corr = nums.corr().stack().reset_index().rename(columns={'level_0':'x','level_1':'y',0:'corr'})
            heat = alt.Chart(corr).mark_rect().encode(
                x='x:N', y='y:N', color=alt.Color('corr:Q', scale=alt.Scale(scheme='viridis')), tooltip=['x','y','corr']
            ).properties(width=600,height=400)
            st.altair_chart(heat)
            st.subheader("Compenso per Corsa e Autista")
            comp = df_filtered[['ID VR','Conducente','Costo_Num']].rename(columns={'Costo_Num':'Costo (€)'})
            st.dataframe(comp)

    with tabs[4]:  # Flussi Orig-Dest
        st.header("🚛 Origine → Destinazione")
        if 'Sequenza delle strutture' in df_filtered:
            seq = df_filtered['Sequenza delle strutture'].str.split('->', expand=True)
            df_filtered['Origine'], df_filtered['Destinazione'] = seq[0], seq[1]
        if {'Origine','Destinazione'}.issubset(df_filtered.columns):
            flow = df_filtered.groupby(['Origine','Destinazione']).size().reset_index(name='Count')
            st.dataframe(flow.sort_values('Count',ascending=False).head(50))

if __name__ == '__main__':
    main()
