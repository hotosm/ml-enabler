import datetime

class VersionExists(Exception):
    pass

class NotFound(Exception):
    """ Custom exception to indicate model not found in database"""
    pass

class VersionNotFound(Exception):
    """ Custom exception to indicate that model version is not found """
    pass


class ImageryNotFound(Exception):
    """ Custom exception to indicate that imagery was not found """

class IntegrationNotFound(Exception):
    """ Custom exception to indicate that imagery was not found """

class PredictionsNotFound(Exception):
    """ Custom exception to indicate that no predictions were found """


def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh
    timestamp when new models initialised"""
    return datetime.datetime.utcnow()

