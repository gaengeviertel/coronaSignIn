# Simple Sign-In system to comply with Hamburg, Germany corona regulations

Open questions:
- Database Backups
- A better pod definition (kube yaml? would that actually be better?)

ToDos:
- Make it look nicer
- Some more features from the list with the link I don't have

## Dev Setup

The application requires Python version 3.8.
With `direnv` installed, you only need to install pipenv and then you're set.

Otherwise, you need to install `pipenv` first. Then, install the dependencies
using `pipenv install`. You can run the project in development mode using
`env FLASK_ENV=development pipenv run flask run`. You will also need to provide the following environment variables: `CORONA_SIGN_IN_SECRET_KEY`, `CORONA_SIGN_IN_DATABASE_URI`.

## Configuration

Copy the `config.py.example` to `config.py` and adjust the relevant values.

## Database

Run `flask db upgrade`.


## Deployment

### Building the docker image

Since pipenv is awkward in docker, you need to run `pipenv lock -r
> requirements.txt` before running `podman build -t corona-sign-in .` (Or
docker instead of podman if you prefer that)

Don't forget to re-generate requirements.txt if you install new dependencies!

### Migrating the database

NOTE: if you want to use something besides postgres, additional dependencies
might need to be installed

`podman run -e CORONA_SIGN_IN_DATABASE_URI=postgresql://user:pw@host/database
corona-sign-in flask db upgrade`

### Running the application

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

#### Get a database shell

podman container run -ti --rm --pod corona-sign-in postgres -h localhost -U corona-sign-in corona-sign-in
