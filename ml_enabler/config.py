import os
from dotenv import load_dotenv

class EnvironmentConfig:
    """ Base configuration class """

    load_dotenv(os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', 'ml_enabler.env')
    ))

    # One of 'docker' or 'aws'
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'docker');

    SECRET_KEY = os.getenv('SECRET_KEY', 'secretkey');

    # Database connection
    POSTGRES_USER = os.getenv('POSTGRES_USER', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
    POSTGRES_ENDPOINT = os.getenv('POSTGRES_ENDPOINT', 'postgresql')
    POSTGRES_DB = os.getenv('POSTGRES_DB', None)
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

    MACHINE_AUTH=os.getenv('MACHINE_AUTH', None)
    ASSET_BUCKET=os.getenv('ASSET_BUCKET', None)
    STACK=os.getenv('STACK', None)
    GitSha=os.getenv('GitSha', None)
    MAPBOX_TOKEN=os.getenv('MAPBOX_TOKEN', None)

    if ENVIRONMENT == 'aws':
        if GitSha is None:
            print("GitSha Env Var Required")
            raise
        if MACHINE_AUTH is None:
            print("MACHINE_AUTH Env Var Required")
            raise
        if STACK is None:
            print("STACK Env Var Required")
            raise
        if ASSET_BUCKET is None:
            print("ASSET_BUCKET Env Var Required")
            raise

    if MAPBOX_TOKEN is None:
        print("MAPBOX_TOKEN Env Var Required")
        raise

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
