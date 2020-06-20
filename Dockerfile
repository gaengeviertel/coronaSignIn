# pipenv is a bit of a pain in the final image, so we use a separate stage to
# generate the requirements.txt. This should be cached unless we update or add
# dependencies.
FROM python:3.8 as mkrequirementstxt
RUN pip install pipenv
WORKDIR /workdir
COPY Pipfile Pipfile.lock .
RUN pipenv lock -r > requirements.txt


FROM python:3.8

MAINTAINER simon.kohlmeyer@gmail.com

COPY --from=mkrequirementstxt /workdir/requirements.txt /

RUN pip install waitress psycopg2 -r /requirements.txt

COPY . /app
WORKDIR /app


CMD ["waitress-serve", "--call", "app:create_app"]
