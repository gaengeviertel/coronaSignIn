![CI](https://github.com/voidus/coronaSignIn/workflows/CI/badge.svg)
# Simple Sign-In system to comply with Hamburg, Germany corona regulations

As of July 2020, Hamburg (Germany) requires bars, pubs and the like to record
the names and contact data for all visitors to help with COVID-19 contact
tracing. This application allows guests to fill in their data on their phones.

**IMPORTANT**: This document contains suggestions on how to deal with this
regulation, but we are no legal professional. Just as the rest of this software,
this document is provided *as-is*, with **no guarantees at all**, including for
correctness of information or absence of critical bugs.

Nonetheless, we hope this is helpful, but you need to decide if there is an
unacceptable risk for you.

**ALSO IMPORTANT**: This document often refers to 21 days, while the regulation
requires you to produce data for the last 14 days. This is so that you have
a window in which to respond: If the data is automatically deleted after 14
days, you need to extract the data on the day you get the request.
It is currently unclear whether this is necessary. Please use your own
judgement.

## Architecture

The application will write the data into an PostgreSQL database. At the moment
we only officially support deployment on podman, but we assume that docker and
platforms such as kubernetes should work fine. If you are interested in running
this application and need any support, don't hesitate to [create an issue](https://github.com/voidus/coronaSignIn/issues)

## Deployment

**Important**: Please make sure to follow the Production Checklist if you deploy
this application!

Build the docker image using `podman build -t corona-sign-in .`

The application needs a postgresql database. We currently do not provide
a production-grade pod definition, but looking into `kube-dev.yml` should tell
you how the application can be run.

You need to **migrate the database** before you can use the service:

```
podman exec corona-sign-in-app \
    flask db upgrade
```

If you struggle with setting things up and require more instructions, please
[let us know](https://github.com/voidus/coronaSignIn/issues).

### Production Checklist

Please make sure to take care of the following topics before going live. They
are listed first and then discussed in detail.

- **Backups**: You need to make sure that you can provide the data in case the
    Gesundheitsamt requests it.
- **Data pruning**: The regulations require you to provide data for the previous
    two weeks in the case of a known case of COVID-19, so you shouldn't store
    forever.

#### Backups
We suggest to set up a cronjob to export data as described below. In order to
prune the stored data, you also need to delete old backups.

Please be aware that the oldest data you store is the age of the oldest entry in
the database plus the age of your oldest backup.

#### Data pruning

This deletes all entries that are older than 21 days. This should be run in
a cronjob. Please test this thoroughly! If you accidentally delete data earlier
than you mean to, you won't be able to produce it in case of a COVID-19
infection!

```
podman exec corona-sign-in-db \
    psql -h localhost -U corona-sign-in corona-sign-in \
    --command 'DELETE FROM sign_ins WHERE DATE_PART('day', NOW() - date) > 21;'
```

To delete backups older than 7 days, you can use the following command. Please
make sure you understand it before running so you don't accidentally delete
important things!

`find /path/to/backups -mtime +7 -print0 | xargs -0 rm`

This should also run in a cronjob. All in all, this means that you store data
for *4 weeks* if you followed the suggestions in this document. (The oldest
backup will be a week old, and it will contain data from 21 days before that.)

### How to export data

This gets all saved sign-ins and stores them in a file named like
`corona-sign-in-2020-07-02.csv`. Test this after setting everything up, you
might need to adjust the pod name or postgresql credentials!

```
podman exec corona-sign-in-db \
    psql -h localhost -U corona-sign-in corona-sign-in \
    --csv --command 'SELECT * FROM sign_ins;' \
    > "corona-sign-in-$(date -I).csv"
```

## Dev Setup

The application requires Python version 3.8.
With `direnv` installed, you only need to install pipenv and then you're set.

Otherwise, you need to install `pipenv` first. Then, install the dependencies
using `pipenv install`.
You can run the project in development mode using
```
env \
    FLASK_ENV=development \
    CORONA_SIGN_IN_SECRET_KEY="insecure secret key" \
    CORONA_SIGN_IN_DATABASE_URI="sqlite:///${PWD}/db.sqlite" \
    pipenv run flask run
```

If you have direnv installed (highly recommended), this will work automatically,
and you can start the dev server using `flask run`

### Tests

Run the tests using `pipenv run pytest`. You can also auto-rerun tests while
you're changing code with `pipenv run invoke tdd`. It will only re-run tests
affected by your changes, so it should be a pretty good feedback loop.

Note: You need to have chromedriver installed for the selenium tests. If that is
not the case, you can run all non-selenium tests using `pytest -m 'not slow'`

### Style

Use (black)[https://github.com/ambv/black] to format your code. It will be
installed as part of the dev dependencies.

### Pre-Commit

To automatically run black and check for a few other common issues on commit,
run `pre-commit install`. It is installed as part of the dev requirements and
will set everything up. You only ever need to run it once.

## Configuration

Configuration is done via environment variables. Have a look at `src/config.py`,
kube-dev.yml or the examples in this readme to see which configuration options
are possible.

### Running the application manually

1. Build the image
    `podman build -t corona-sign-in .`
2. Create the pod
    `podman pod create --name corona-sign-in --publish 8080:8080`
3. Run the database
    `podman container run -d --name corona-sign-in-db --pod corona-sign-in -e POSTGRES_PASSWORD=pass -e POSTGRES_USER=corona-sign-in -e POSTGRES_DB=corona-sign-in postgres`
4. Migrate the database
    `podman container run --pod corona-sign-in -e CORONA_SIGN_IN_DATABASE_URI="postgresql://corona-sign-in:pass@localhost/corona-sign-in" -e CORONA_SIGN_IN_SECRET_KEY="irrelevant" corona-sign-in flask db upgrade`
5. Run the application
    `podman container run -d --pod corona-sign-in -e CORONA_SIGN_IN_DATABASE_URI="postgresql://corona-sign-in:pass@localhost/corona-sign-in" -e CORONA_SIGN_IN_SECRET_KEY="irrelevant" corona-sign-in`

### Running the application using the kube file

1. Build the image
    `podman build -t corona-sign-in .`
2. Load the kube file
    `podman play kube kube-dev.yml`
3. Migrate the database
    `podman exec corona-sign-in-app flask db upgrade`

#### Get a database shell

`podman container run -ti --rm --pod corona-sign-in postgres -h localhost -U corona-sign-in corona-sign-in`
