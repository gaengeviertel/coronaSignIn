# Create a reasonably secure secret key using `python -c import os; print (os.urandom(128))`
import os

secret_key = os.environ["CORONA_SIGN_IN_SECRET_KEY"]
sqlalchemy_database_uri = os.environ["CORONA_SIGN_IN_DATABASE_URI"]
