# Simple Sign-In system to comply with Hamburg, Germany corona regulations

## Development

Copy the `config.py.example` to `config.py` and adjust the relevant values.

With `direnv` and `nix` installed, you can `direnv allow`, install the
dependencies with `pipenv install` and start the dev server with `flask run`.

Otherwise, you need to install `pipenv` first. Then, install the dependencies
using `pipenv install`. You can run the project in development mode using
`env FLASK_ENV=development pipenv run flask run`.

## Deployment

TBD

## Database setup

TBD
