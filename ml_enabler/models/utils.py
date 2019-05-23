import datetime


class NotFound(Exception):
    """ Custom exception to indicate model not found in database"""
    pass


def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh
    timestamp when new models initialised"""
    return datetime.datetime.utcnow()
