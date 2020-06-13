# Simple Sign-In system to comply with Hamburg, Germany corona regulations

## Dev Setup

With `direnv` installed, you only need to install pipenv and then you're set.

Otherwise, you need to install `pipenv` first. Then, install the dependencies
using `pipenv install`. You can run the project in development mode using
`env FLASK_ENV=development pipenv run flask run`.

## Configuration

Copy the `config.py.example` to `config.py` and adjust the relevant values.

## Database

Run `flask db upgrade`.


## Deployment

TBD
