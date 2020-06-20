# Create a reasonably secure secret key using `python -c import os; print (os.urandom(128))`
import os


class Config:
    SECRET_KEY = os.environ["CORONA_SIGN_IN_SECRET_KEY"]
    SQLALCHEMY_DATABASE_URI = os.environ["CORONA_SIGN_IN_DATABASE_URI"]

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    """ This makes a deprecation warning go away. It doesn't change behaviour"""
