import streamlit as st
import openai

# Assicurati di avere i pacchetti necessari installati:
# pip install streamlit openai

# Config
openai.api_key = st.secrets['OPENAI']['api_key']

st.set_page_config(page_title="Multi-AI Assistants", layout="wide")

# Sidebar: scegli assistente
st.sidebar.title("Seleziona Assistente AI")
assistant_options = {
    "Assistente Generico": {"model": "gpt-4"},
    "Assistente Esperto in Python": {"model": "gpt-3.5-turbo", "system": "You are a helpful Python coding expert."},
    "Assistente Medico": {"model": "gpt-3.5-turbo", "system": "You are a professional medical assistant. Provide general advice, not diagnosis."}
}
assistant_name = st.sidebar.selectbox("Assistente", list(assistant_options.keys()))
assistant_config = assistant_options[assistant_name]

# State
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Titolo pagina
st.title(f"Chat con {assistant_name}")

# Mostra conversazione
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.markdown(f"**Tu:** {msg['content']}")
    else:
        st.markdown(f"**{assistant_name}:** {msg['content']}\n")

# Input utente
user_input = st.text_input("Scrivi qui il tuo messaggio...", key='input')
send = st.button("Invia")

if send and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Prepara messaggi
    messages = []
    if 'system' in assistant_config:
        messages.append({"role": "system", "content": assistant_config['system']})
    messages.extend(st.session_state.messages)
    # Chiamata OpenAI
    with st.spinner("In corso..."):
        response = openai.ChatCompletion.create(
            model=assistant_config['model'],
            messages=messages,
            temperature=0.7
        )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.input = ''

# Footer e istruzioni
instructions = '''**Istruzioni:**

1. Salva questo file come **app.py**

2. Crea il file **.streamlit/secrets.toml** con dentro:
```
[OPENAI]
api_key = "LA_TUA_CHIAVE"
```

3. Crea **requirements.txt** con:
```
streamlit
openai
```

4. Installa dipendenze:
```
pip install -r requirements.txt
```

5. Esegui:
```
streamlit run app.py
```'''
st.sidebar.markdown(instructions)

st.sidebar.markdown("Powered by OpenAI & Streamlit")
