FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y curl && \
    pip install flask docker requests && \
    apt-get clean

COPY app.py /app/app.py
COPY update_dns.py /app/update_dns.py
COPY event_listener.py /app/event_listener.py

CMD ["python", "app.py"]
