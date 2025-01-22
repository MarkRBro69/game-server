FROM python:3.11

WORKDIR /app

COPY ./game_service /app
COPY ./requirements.txt /app/requirements.txt
COPY ./config.py /app/config.py
COPY ./docker_env /app

RUN pip install --upgrade pip

RUN pip install -r /app/requirements.txt

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
