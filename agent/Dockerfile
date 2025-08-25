FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN export PYTHONPATH=/app:$PYTHONPATH

ENV GOOGLE_API_KEY key
ENV MCP_PATH http://localhost:8000/mcp
ENV PORT 8000
ENV RABBIT_CONNECTION amqp://guest:guest@localhost:5672/

CMD ["sh", "-c", "export PYTHONPATH=/app:$PYTHONPATH && uvicorn agent:app --host 0.0.0.0"]