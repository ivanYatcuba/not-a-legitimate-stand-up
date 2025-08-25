import os

import uvicorn
from loguru import logger

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting server on port {os.environ.get("MCP_PATH")}")
    uvicorn.run("agent:app", host="0.0.0.0", port=port, log_config=None)
