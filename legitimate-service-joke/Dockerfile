FROM nvidia/cuda:13.0.0-cudnn-devel-ubuntu24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3-pip \
    git \
    build-essential

RUN pip3 install --break-system-packages torch==2.8.0

WORKDIR /app
COPY ./requirements.txt /app

RUN pip3 install --break-system-packages packaging
RUN apt-get install python3-dev -y
RUN pip3 install --break-system-packages -r requirements.txt

RUN pip3 install --break-system-packages git+https://github.com/One-sixth/fairseq.git
RUN pip3 install --break-system-packages git+https://github.com/patriotyk/ipa-uk.git
RUN pip3 install --break-system-packages git+https://github.com/patriotyk/styletts2-inference.git
RUN pip3 install --break-system-packages git+https://github.com/patriotyk/ukrainian-word-stress.git
RUN apt-get install ffmpeg -y

COPY . /app

RUN export PYTHONPATH=/app:$PYTHONPATH

ENV RABBIT_CONNECTION amqp://guest:guest@localhost:5672/

CMD ["sh", "-c", "export PYTHONPATH=/app:$PYTHONPATH && python3 /app/main.py"]