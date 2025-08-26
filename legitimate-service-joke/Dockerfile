FROM pytorch/pytorch

RUN conda update -n base -c defaults conda && \
    conda install -y python=3.12 && \
    conda update --all --yes \

RUN python -m pip install --upgrade pip==24.
RUN pip3 install -r requirements.txt

WORKDIR /app

COPY . /app

RUN export PYTHONPATH=/app:$PYTHONPATH

ENV RABBIT_CONNECTION amqp://guest:guest@localhost:5672/

CMD ["sh", "-c", "export PYTHONPATH=/app:$PYTHONPATH && python /app/main.py"]