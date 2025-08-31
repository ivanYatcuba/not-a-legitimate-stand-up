import asyncio
import json
import sys
import threading

import aiormq
from aiormq.abc import AbstractChannel
from loguru import logger

import env
from env import RABBIT_CONNECTION
from joke.joke_generator import JokeGenerator
from mcpserver import JokeMcpServer

joke_generator: JokeGenerator | None

async def on_message(message: aiormq.abc.DeliveredMessage):
    logger.info(f'Message body is: {message.body!r}')

    msg = json.loads(message.body)

    if len(msg['topic']) > 0:
        joke = joke_generator.tell_topic_joke(msg['topic'])
    else:
        joke = joke_generator.tell_generic_joke()

    await message.channel.basic_publish(
        json.dumps({'joke': joke, 'user_id': msg['user_id']}).encode(),
        routing_key='joke.prepared',
        exchange=''
    )


async def run_rabbit_consumer():
    connection = await aiormq.connect(RABBIT_CONNECTION)

    channel = await connection.channel()
    await channel.queue_declare('joke.prepared', durable=True)
    declare_ok = await channel.queue_declare('joke.generate', durable=True)
    logger.info('start listening to queue')
    await channel.basic_consume(
        declare_ok.queue, on_message, no_ack=True
    )


async def run_mcp(rabbit_channel: AbstractChannel):
    try:
        logger.info('starting MCP server')
        server = JokeMcpServer(rabbit_channel)
        await server.start()
    except KeyboardInterrupt:
        await asyncio.sleep(1)


def run_loop_in_thread(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


async def main():
    logger.info('starting init joke generator')
    global joke_generator
    joke_generator = JokeGenerator(env.JOKE_LLM, env.JOKE_TTS_MODEL_PATH)
    logger.info('joke generator inited')

    connection = await aiormq.connect(RABBIT_CONNECTION)

    channel = await connection.channel()

    loop = asyncio.new_event_loop()
    thread = threading.Thread(target=run_loop_in_thread, args=(loop,))
    thread.start()

    asyncio.run_coroutine_threadsafe(run_rabbit_consumer(), loop)

    await run_mcp(channel)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.error('Interrupted')
        sys.exit(0)
