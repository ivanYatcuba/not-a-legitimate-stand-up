import os

from dotenv import load_dotenv

load_dotenv()

RABBIT_CONNECTION = os.environ.get('RABBIT_CONNECTION')
MCP_PORT = int(os.getenv('MCP_PORT', 8000))

JOKE_LLM = os.environ.get('JOKE_LLM')
JOKE_TTS_MODEL_PATH = os.environ.get('JOKE_TTS_MODEL_PATH')

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_BUCKET = os.environ.get('AWS_BUCKET')
