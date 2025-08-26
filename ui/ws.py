import json

import streamlit as st
import websocket
from loguru import logger
from streamlit.runtime import Runtime
from streamlit.runtime.app_session import AppSession

from env import WS_PATH


def get_streamlit_sessions() -> list[AppSession]:
    runtime: Runtime = Runtime.instance()
    return [s.session for s in runtime._session_mgr.list_sessions()]


def notify() -> None:
    for session in get_streamlit_sessions():
        session._handle_rerun_script_request()


def on_message(ws, message):
    logger.info(f"ws message: {message}")

    json_message = json.loads(message)
    st.session_state.messages.append({"role": "assistant", "content": json_message['message']})
    notify()


def on_error(ws, error):
    logger.info(f"ws error: {error}")


def on_close(ws, close_status_code, close_msg):
    logger.info("ws connection closed")


def on_open(ws):
    st.session_state.websocket_connection = ws
    logger.info("ws opened")


def run_websocket(thread_id: str):
    logger.info(f"Starting websocket on {WS_PATH}/{thread_id}")
    ws = websocket.WebSocketApp(
        f"{WS_PATH}/{thread_id}",
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()
