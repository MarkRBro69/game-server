FROM python:3.11

WORKDIR /app

COPY frontend_service /app
COPY requirements.txt /app/requirements.txt
COPY config.py /app/config.py
COPY frontend_service/docker_env /app

RUN pip install --upgrade pip

RUN pip install -r /app/requirements.txt

RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
