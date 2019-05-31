import datetime
from shapely.geometry import box
from geoalchemy2 import Geometry
from geoalchemy2.functions import GenericFunction


class NotFound(Exception):
    """ Custom exception to indicate model not found in database"""
    pass


class VersionNotFound(Exception):
    """ Custom exception to indicate that model version is not found """
    pass


def timestamp():
    """ Used in SQL Alchemy models to ensure we refresh
    timestamp when new models initialised"""
    return datetime.datetime.utcnow()


def version_to_array(version: str):
    """ Convert a semver string into it's components as integers """

    version_array = version.split('.')
    version_major = version_array[0]
    version_minor = version_array[1] or 0
    version_patch = version_array[2] or 0

    return [version_major, version_minor, version_patch]


class ST_GeomFromText(GenericFunction):
    """ Export the postgis ST_GeomFromText function """
    name = 'ST_GeomFromText'
    type = Geometry


def bbox_to_polygon_wkt(bbox: list):
    """ Get a polygon from the bbox """

    return box(bbox[0], bbox[1], bbox[2], bbox[3]).wkt