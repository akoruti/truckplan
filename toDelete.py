import streamlit as st
import yaml
import os

# ——————————————————————————
# Config
# ——————————————————————————
STORAGE_FILE = "regole.yaml"

# ——————————————————————————
# Funzioni di I/O
# ——————————————————————————
def carica_regole():
    if not os.path.exists(STORAGE_FILE):
        st.error(f"⚠️ File di regole non trovato: {STORAGE_FILE}")
        return {}
    with open(STORAGE_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

def salva_regole(regole):
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            # sort_keys=False per preservare l’ordine definito
            yaml.dump(regole, f, allow_unicode=True, sort_keys=False)
    except Exception as e:
        st.error(f"❌ Errore salvataggio YAML: {e}")

# ——————————————————————————
# Configurazione pagina
# ——————————————————————————
st.set_page_config(
    page_title="AI Viaggi Manager",
    page_icon="🗺️",
    layout="centered"
)

st.title("🗺️ AI Viaggi Manager")
st.markdown("Interfaccia Streamlit per gestire le regole AI di programmazione viaggi.")

# ——————————————————————————
# Carica e mostra le regole
# ——————————————————————————
regole = carica_regole()
if not regole:
    st.stop()

sezione = st.selectbox("📂 Seleziona sezione", list(regole.keys()))
st.subheader(f"📖 Dettagli: `{sezione}`")
st.json(regole[sezione])

# ——————————————————————————
# Area di modifica (dev/demo)
# ——————————————————————————
st.markdown("---")
st.markdown("### ✏️ Modifica YAML della sezione")
yaml_input = st.text_area(
    "Editor YAML",
    value=yaml.dump(regole[sezione], allow_unicode=True, sort_keys=False),
    height=300
)

if st.button("💾 Salva modifiche"):
    try:
        nuovi_dati = yaml.safe_load(yaml_input)
        regole[sezione] = nuovi_dati
        salva_regole(regole)
        st.success("✅ Sezione aggiornata correttamente!")
    except yaml.YAMLError as ye:
        st.error(f"❌ Formato YAML non valido:\n{ye}")
    except Exception as e:
        st.error(f"❌ Errore inaspettato: {e}")
