FROM python:3.10-slim

WORKDIR /web-app

COPY requirements.txt .

RUN pip install -r requirements

COPY . .

CMD uvicorn main:app