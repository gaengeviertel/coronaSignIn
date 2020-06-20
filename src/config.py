# Create a reasonably secure secret key using `python -c import os; print (os.urandom(128))`
import os


class ProductionConfig:
    @property
    def SECRET_KEY(self):
        return os.environ["CORONA_SIGN_IN_SECRET_KEY"]

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.environ["CORONA_SIGN_IN_DATABASE_URI"]

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """ This makes a deprecation warning go away. It doesn't change behaviour"""


class TestConfig(ProductionConfig):
    SECRET_KEY = "insecure secret key for testing"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
