import json
import logging
import os
from logging import getLogger

import streamlit as st
import websocket
from streamlit.runtime import Runtime
from streamlit.runtime.app_session import AppSession

app_logger = getLogger()
app_logger.addHandler(logging.StreamHandler())
app_logger.setLevel(logging.INFO)


def get_streamlit_sessions() -> list[AppSession]:
    runtime: Runtime = Runtime.instance()
    return [s.session for s in runtime._session_mgr.list_sessions()]

def notify() -> None:
    for session in get_streamlit_sessions():
        session._handle_rerun_script_request()

def on_message(ws, message):
    app_logger.info(f"ws message: {message}")

    json_message = json.loads(message)
    st.session_state.messages.append({"role": "assistant", "content": json_message['message']})
    with st.chat_message('assistant'):
        st.markdown(json_message["message"])
    notify()


def on_error(ws, error):
    app_logger.info(f"ws error: {error}")


def on_close(ws, close_status_code, close_msg):
    app_logger.info("ws connection closed")


def on_open(ws):
    st.session_state.websocket_connection = ws
    app_logger.info("ws opened")


def run_websocket(thread_id: str):
    app_logger.info(f"Starting websocket on {os.environ.get('WS_PATH')}/{thread_id}")
    ws = websocket.WebSocketApp(
        f"{os.environ.get("WS_PATH")}/{thread_id}",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()
