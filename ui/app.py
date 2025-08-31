import threading
import uuid

from streamlit.runtime.scriptrunner import add_script_run_ctx

from ws import *
from env import AVATAR_PATH

if "websocket_thread" not in st.session_state:
    print("WebSocket thread not found")
    st.session_state.websocket_thread = None

if "websocket_connection" not in st.session_state:
    print("websocket_connection not found")
    st.session_state.websocket_connection = None

if "messages" not in st.session_state:
    st.session_state.messages = []

def print_msg(role: str, msg: str):
    with st.chat_message(role, avatar=AVATAR_PATH if role == "assistant" else None):
        if msg.startswith("https://"):
            st.audio(msg)
        else:
            st.markdown(msg)

if st.session_state.websocket_thread is None or not st.session_state.websocket_thread.is_alive():
    print("Starting WebSocket connection...")
    websocket_thread = threading.Thread(target=run_websocket, daemon=True, args=(str(uuid.uuid4()),))
    add_script_run_ctx(websocket_thread)
    websocket_thread.start()
    st.session_state.websocket_thread = websocket_thread

st.title("Not a legimate joker")

for message in st.session_state.messages:
    print_msg(message["role"], message["content"])

if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    print_msg("user", prompt)
    st.session_state.websocket_connection.send(json.dumps({"question": prompt}))
