import multiprocessing

import pytest

from app import create_app, db
from config import TestConfig

# This is needed to make the tests work on py3.8 + macOS catalina
# See https://github.com/pytest-dev/pytest-flask/issues/104
multiprocessing.set_start_method("fork")


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig())
    with app.app_context():
        yield app


@pytest.fixture
def _db(app):
    # Make sure this is actually the testing database
    assert db.engine.url.drivername == "sqlite"
    assert db.engine.url.database.endswith("/testing.sqlite")
    db.drop_all()

    db.create_all()

    return db


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument("--headless")
    return firefox_options


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument("--headless")
    return chrome_options
