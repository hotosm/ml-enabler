import os
from dotenv import load_dotenv

class EnvironmentConfig:
    """ Base configuration class """

    load_dotenv(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'ml_enabler.env')
    ))

    # Database connection
    POSTGRES_USER = os.getenv('POSTGRES_USER', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
    POSTGRES_ENDPOINT = os.getenv('POSTGRES_ENDPOINT', 'postgresql')
    POSTGRES_DB = os.getenv('POSTGRES_DB', None)
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

    ASSET_BUCKET=os.getenv('ASSET_BUCKET', None)
    STACK=os.getenv('STACK', 'ml-enabler-staging')
    GitSha=os.getenv('GitSha', None)

    if GitSha is None:
        print("GitSha Env Var Required")
        raise

    MAPBOX_TOKEN=os.getenv('MAPBOX_TOKEN', None)

    if os.getenv('MLENABLER_DB', False):
        SQLALCHEMY_DATABASE_URI = os.getenv('MLENABLER_DB', None)
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}' +  \
                                    f':{POSTGRES_PASSWORD}' + \
                                    f'@{POSTGRES_ENDPOINT}:' + \
                                    f'{POSTGRES_PORT}' + \
                                    f'/{POSTGRES_DB}'

        SQLALCHEMY_TRACK_MODIFICATIONS = False


class TestConfig(EnvironmentConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv('MLENABLER_TEST_DB', 'postgresql://admin@127.0.0.1/ml_enabler_test')
