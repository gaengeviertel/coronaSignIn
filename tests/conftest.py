import pytest

from app import create_app
from config import TestConfig


@pytest.fixture(scope="session")
def app():
    return create_app(TestConfig())


@pytest.fixture
def firefox_options(firefox_options):
    firefox_options.add_argument("--headless")
    return firefox_options


@pytest.fixture
def chrome_options(chrome_options):
    chrome_options.add_argument("--headless")
    return chrome_options
