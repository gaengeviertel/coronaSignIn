import os
import flask
import unittest.mock as mock

from config import ProductionConfig


def test_gets_location_from_environment():
    with mock.patch.dict(
        os.environ,
        {
            "CORONA_SIGN_IN_LOCATIONS": "here ; there; everywhere else",
            "CORONA_SIGN_IN_DATABASE_URI": "",
        },
    ):
        config = flask.Config("")
        config.from_object(ProductionConfig())
        assert config["LOCATIONS"] == [
            "here",
            "there",
            "everywhere else",
        ]
