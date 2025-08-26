import os

from dotenv import load_dotenv

load_dotenv()

PORT = int(os.getenv('AGENT_PORT', 8000))
RABBIT_CONNECTION = os.environ.get('RABBIT_CONNECTION')
MCP_PATH = os.environ.get('MCP_PATH')