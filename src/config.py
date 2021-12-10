# Create a reasonably secure secret key using `python -c import os; print (os.urandom(128))`
import os


class ProductionConfig:
    WTF_CSRF_ENABLED = False

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return os.environ.get("CORONA_SIGN_IN_DATABASE_URI")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """ This makes a deprecation warning go away. It doesn't change behaviour"""

    @property
    def LOCATIONS(self):
        locations_raw = os.environ.get("CORONA_SIGN_IN_LOCATIONS")
        if locations_raw:
            return [s.strip() for s in locations_raw.split(";")]
        else:
            return None


class TestConfig(ProductionConfig):
    ENV = "test"
    SECRET_KEY = "insecure secret key for testing"
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.path.dirname(os.path.dirname(__file__))}/testing.sqlite"
    )
    LOCATIONS = None
