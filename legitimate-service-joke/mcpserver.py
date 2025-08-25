import json
from typing import Annotated, Optional

from aiormq.abc import AbstractChannel
from loguru import logger
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts import Prompt
from pydantic import BaseModel


class JokeScheduleResponse(BaseModel):
    is_schedule_successful: bool


class JokeMcpServer:
    def __init__(self, rabbit_channel: AbstractChannel):
        self.joke_mcp_server = FastMCP("JokeGenerator", host="0.0.0.0", port=8080)
        self.rabbit_channel = rabbit_channel

        self.joke_mcp_server.add_prompt(Prompt(name='system_prompt', fn=self.system_prompt))
        self.joke_mcp_server.add_tool(
            self.joke,
            name='joke_tool',
            description='Schedule joke generation on provided topic that could be empty',
        )

    def system_prompt(self):
        return 'You are funny AI assistant use the tools if needed. Your responses must be in Ukrainian only'

    async def joke(self, topic: Optional[Annotated[str, 'joke topic']], context: Context) -> JokeScheduleResponse:
        try:
            user_id = context.request_context.request.headers.get('user_id')
            if not user_id:
                raise ValueError('no auth info provided')
            logger.info(f'scheduling job for topic {topic}')
            await self.rabbit_channel.basic_publish(
                json.dumps({'topic': topic, 'user_id': user_id}).encode(),
                routing_key='joke.generate',
                exchange=''
            )
            return JokeScheduleResponse.model_validate({'is_schedule_successful': True})
        except Exception as e:
            logger.error('error scheduling job', e)
            return JokeScheduleResponse.model_validate({'is_schedule_successful': False})

    async def start(self):
        return await self.joke_mcp_server.run_streamable_http_async()
