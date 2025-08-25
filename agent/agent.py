import asyncio
import json
import os
import threading
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, List

import aiormq
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.chat_models import init_chat_model
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.prompts import load_mcp_prompt
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import tools_condition, ToolNode
from loguru import logger
from mcp import ClientSession
from pydantic import BaseModel
from starlette.websockets import WebSocket
from typing_extensions import TypedDict

load_dotenv()

websocket_clients = {}


class State(TypedDict):
    messages: Annotated[List[AnyMessage], add_messages]


class QueryRequest(BaseModel):
    question: str


async def on_message(message: aiormq.abc.DeliveredMessage):
    logger.info(f"Message body is: {message.body!r}")
    msg = json.loads(message.body)
    user_id = msg['user_id']
    global websocket_clients
    if user_id in websocket_clients:
        socket_connection = websocket_clients[user_id]
        await socket_connection.send_text(json.dumps({"message": msg["joke"]}))


async def start_rabbit_listener():
    connection = await aiormq.connect(f"{os.environ.get("RABBIT_CONNECTION")}")
    channel = await connection.channel()
    declare_ok = await channel.queue_declare('joke.prepared', durable=True)

    logger.info('start listening to queue')
    await channel.basic_consume(
        declare_ok.queue, on_message, no_ack=True
    )


def run_loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_loop_in_thread, args=(loop,))
    thread.start()

    asyncio.run_coroutine_threadsafe(start_rabbit_listener(), loop)

    yield


app = FastAPI(lifespan=lifespan)


async def create_graph(joke_tool_session: ClientSession):
    llm = init_chat_model("gemini-2.5-flash", model_provider="google_genai", temperature=0)

    joke_tools = await load_mcp_tools(joke_tool_session)
    llm_with_tool = llm.bind_tools(joke_tools)

    system_prompt = await load_mcp_prompt(joke_tool_session, "system_prompt")
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt[0].content),
        MessagesPlaceholder("messages")
    ])
    chat_llm = prompt_template | llm_with_tool

    def chat_node(state: State) -> State:
        state["messages"] = chat_llm.invoke({"messages": state["messages"]})
        return state

    graph_builder = StateGraph(State[AnyMessage])
    graph_builder.add_node("chat_node", chat_node)
    graph_builder.add_node("tool_node", ToolNode(tools=joke_tools))
    graph_builder.add_edge(START, "chat_node")
    graph_builder.add_conditional_edges("chat_node", tools_condition, {"tools": "tool_node", "__end__": END})
    graph_builder.add_edge("tool_node", "chat_node")
    graph = graph_builder.compile(checkpointer=MemorySaver())
    return graph


@app.websocket("/ws/{thread_id}")
async def websocket_endpoint(websocket: WebSocket, thread_id: str):
    user_id = str(uuid.uuid4())
    logger.info(f'opened socket connection with id {thread_id}, user id: {user_id}')
    await websocket.accept()

    client = MultiServerMCPClient(
        {
            "joke_tool": {
                "url": f'{os.environ.get("MCP_PATH")}',
                "transport": "streamable_http",
                "headers": {"user_id": user_id}
            }
        }
    )
    global websocket_clients
    websocket_clients[user_id] = websocket
    async with client.session("joke_tool") as joke_tool:
        agent = await create_graph(joke_tool)
        try:
            while True:
                data = await websocket.receive_text()
                response = await agent.ainvoke({"messages": data}, config={"configurable": {"thread_id": thread_id}})
                await websocket.send_text(json.dumps({"message": response["messages"][-1].content}))
        except Exception:
            del websocket_clients[user_id]
