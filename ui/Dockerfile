FROM python:3.12

WORKDIR /app

COPY . /app

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

RUN export PYTHONPATH=/app:$PYTHONPATH

ENV WS_PATH ws://localhost:8080/ws

CMD ["sh", "-c", "export PYTHONPATH=/app:$PYTHONPATH && streamlit run /app/app.py"]