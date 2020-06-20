import pytest

from app import create_app
from config import TestConfig


@pytest.fixture
def app():
    return create_app(TestConfig())
