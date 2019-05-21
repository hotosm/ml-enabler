import os
from dotenv import load_dotenv


class EnvironmentConfig:
    """ Base configuration class """

    load_dotenv(os.path.normpath(os.path.join(os.path.dirname(__file__),
                '..', 'ml_enabler.env')))

    # Database connection
    POSTGRES_USER = os.getenv('POSTGRES_USER', None)
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', None)
    POSTGRES_ENDPOINT = os.getenv('POSTGRES_ENDPOINT', 'postgresql')
    POSTGRES_DB = os.getenv('POSTGRES_DB', None)
    POSTGRES_PORT = os.getenv('POSTGRES_PORT', '5432')

    if os.getenv('MLENABLER_DB', False):
        SQLALCHEMY_DATABASE_URI = os.getenv('MLENABLER_DB', None)
    else:
        SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}' +  \
                                    f':{POSTGRES_PASSWORD}' + \
                                    f'@{POSTGRES_ENDPOINT}:' + \
                                    f'{POSTGRES_PORT}' + \
                                    f'/{POSTGRES_DB}'
