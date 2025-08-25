FROM python:3.12

RUN pip3 install --upgrade pip
RUN pip3 install torch
RUN pip3 install -r requirements.txt

WORKDIR /app

COPY . /app

RUN export PYTHONPATH=/app:$PYTHONPATH

ENV RABBIT_CONNECTION amqp://guest:guest@localhost:5672/

CMD ["sh", "-c", "export PYTHONPATH=/app:$PYTHONPATH && python /app/main.py"]