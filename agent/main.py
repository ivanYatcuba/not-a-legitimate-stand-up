import os

import uvicorn
from dotenv import load_dotenv
from loguru import logger

from env import PORT

load_dotenv()

if __name__ == "__main__":
    logger.info(f"Starting server on port {PORT}")
    uvicorn.run("agent:app", host="0.0.0.0", port=PORT, log_config=None)
