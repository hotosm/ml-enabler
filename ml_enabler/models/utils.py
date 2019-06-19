import datetime
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction


class NotFound(Exception):
    """ Custom exception to indicate model not found in database"""
    pass


class VersionNotFound(Exception):
    """ Custom exception to indicate that model version is not found """
    pass


class PredictionsNotFound(Exception):
    """ Custom exception to indicate that no predictions were found """


def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh
    timestamp when new models initialised"""
    return datetime.datetime.utcnow()


class ST_GeomFromText(GenericFunction):
    """ Export the postgis ST_GeomFromText function """
    name = 'ST_GeomFromText'
    type = Geometry


class ST_Intersects(GenericFunction):
    """ Exposes PostGIS ST_Intersects function """
    name = 'ST_Intersects'
    type = Geometry


class ST_MakeEnvelope(GenericFunction):
    """ Exposes PostGIS ST_MakeEnvelope function """
    name = 'ST_MakeEnvelope'
    type = Geometry


class ST_AsText(GenericFunction):
    """ Exposes PostGIS ST_AsText function """
    name = 'ST_AsText'
    type = Geometry
