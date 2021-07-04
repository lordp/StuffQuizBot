# syntax=docker/dockerfile:1

FROM python:3.8-alpine
WORKDIR /code
RUN apk add --no-cache postgresql-dev gcc linux-headers musl-dev g++
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY cogs cogs
COPY bot.py quiz.py startup.sh ./
RUN chmod +x startup.sh
CMD [ "./startup.sh" ]