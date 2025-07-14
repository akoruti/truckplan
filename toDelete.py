import streamlit as st
import openai

# Config
openai.api_key = st.secrets['OPENAI_API_KEY']

st.set_page_config(page_title="Multi-AI Assistants", layout="wide")

# Sidebar: choose assistant
st.sidebar.title("Seleziona Assistente AI")
assistant_options = {
    "Assistente Generico": {"model": "gpt-4"},
    "Assistente Esperto in Python": {"model": "gpt-3.5-turbo", "system": "You are a helpful Python coding expert."},
    "Assistente Medico": {"model": "gpt-3.5-turbo", "system": "You are a professional medical assistant. Provide general advice, not diagnosis."}
}
assistant_name = st.sidebar.selectbox("Assistente", list(assistant_options.keys()))
assistant_config = assistant_options[assistant_name]

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Main UI
st.title(f"Chat con {assistant_name}")

# Display conversation
for msg in st.session_state.messages:
    if msg['role'] == 'user':
        st.markdown(f"**Tu:** {msg['content']}")
    else:
        st.markdown(f"**{assistant_name}:** {msg['content']}")

# User input
user_input = st.text_input("Scrivi qui il tuo messaggio...", key='input')
send = st.button("Invia")

if send and user_input:
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Build messages for OpenAI
    messages = []
    if 'system' in assistant_config:
        messages.append({"role": "system", "content": assistant_config['system']})
    messages.extend(st.session_state.messages)

    # Call OpenAI
    with st.spinner("In corso..."):
        response = openai.ChatCompletion.create(
            model=assistant_config['model'],
            messages=messages,
            temperature=0.7,
        )
    reply = response.choices[0].message.content
    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Clear input
    st.session_state.input = ''

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("Powered by OpenAI & Streamlit")

# Instructions to run
st.sidebar.markdown("**Istruzioni:**\n
1. Salva questo file come app.py\n
2. Imposta la tua chiave API in .streamlit/secrets.toml:\n````
[OPENAI]
api_key = \"LA_TUA_CHIAVE\"
````\n
3. Esegui: `streamlit run app.py`")
