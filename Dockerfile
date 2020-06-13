FROM python:3.8

MAINTAINER simon.kohlmeyer@gmail.com

COPY requirements.txt /

RUN pip install waitress psycopg2 -r /requirements.txt

COPY . /app
WORKDIR /app


CMD ["waitress-serve", "app:app"]
