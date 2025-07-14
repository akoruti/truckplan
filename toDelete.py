# Streamlit Multi-AI Assistants

Questa semplice applicazione Streamlit permette di chattare con differenti "assistenti" basati sui modelli OpenAI. Puoi scegliere tra un assistente generico, un esperto di Python o un assistente medico.

## Preparazione
1. Crea il file `.streamlit/secrets.toml` con la tua API key di OpenAI:
   ```toml
   [OPENAI]
   api_key = "LA_TUA_CHIAVE"
   ```

2. Installa le dipendenze:
   ```bash
   pip install -r requirements.txt
   ```

3. Avvia:
   ```bash
   streamlit run app.py
   ```

L'interfaccia web ti permetterà di scegliere l'assistente desiderato e di iniziare la conversazione.
app.py
Nuovo
+76
-0

import streamlit as st
import openai

# Configura l'API Key di OpenAI nei secrets di Streamlit
openai.api_key = st.secrets['OPENAI']['api_key']

st.set_page_config(page_title="Multi-AI Assistants", layout="wide")

# Sidebar: scelta dell'assistente
st.sidebar.title("Seleziona Assistente AI")
assistant_options = {
    "Assistente Generico": {"model": "gpt-4"},
    "Assistente Esperto in Python": {"model": "gpt-3.5-turbo", "system": "You are a helpful Python coding expert."},
    "Assistente Medico": {"model": "gpt-3.5-turbo", "system": "You are a professional medical assistant. Provide general advice, not diagnosis."}
}
assistant_name = st.sidebar.selectbox("Assistente", list(assistant_options.keys()))
assistant_config = assistant_options[assistant_name]

# Stato della conversazione
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Titolo
st.title(f"Chat con {assistant_name}")

# Conversazione
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.markdown(f"**Tu:** {msg['content']}")
    else:
        st.markdown(f"**{assistant_name}:** {msg['content']}\n")

# Input
user_input = st.text_input("Scrivi qui il tuo messaggio...", key='input')
send = st.button("Invia")

if send and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    messages = []
    if 'system' in assistant_config:
        messages.append({"role": "system", "content": assistant_config['system']})
    messages.extend(st.session_state.messages)
    with st.spinner("In corso..."):
        response = openai.ChatCompletion.create(
            model=assistant_config['model'],
            messages=messages,
            temperature=0.7
        )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.input = ''

# Istruzioni
instructions = '''**Istruzioni:**

1. Crea il file **.streamlit/secrets.toml** contenente:
```
[OPENAI]
api_key = "LA_TUA_CHIAVE"
```

2. Crea **requirements.txt** con:
```
streamlit
openai
```

3. Installa le dipendenze ed esegui l'app con:
```
pip install -r requirements.txt
streamlit run app.py
```
'''

st.sidebar.markdown(instructions)
st.sidebar.markdown("Powered by OpenAI & Streamlit")
