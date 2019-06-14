import datetime
import json
import mercantile
from shapely.geometry import box, Point, shape
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


def bbox_to_polygon_wkt(bbox: list):
    """ Get a polygon from the bbox """

    return box(bbox[0], bbox[1], bbox[2], bbox[3]).wkt


def bbox_str_to_list(bbox: str):
    """ Parse the bbox query param and return a list of floats """

    bboxList = bbox.split(',')
    return list(map(float, bboxList))


def geojson_to_bbox(geojson):
    """ Convert polygon geojson to bbox list """

    polygon = json.loads(geojson)
    bbox = [polygon['coordinates'][0][0][0], polygon['coordinates'][0][0][1], polygon['coordinates'][0][2][0], polygon['coordinates'][0][2][1]]
    return bbox


def point_list_to_wkt(centroid: list):
    """ Convert a python list x,y to WKT """

    return f'SRID=4326;{Point(centroid[0], centroid[1]).wkt}'


def bbox_to_quadkeys(bbox: list, zoom: int):
    """ Find all quadkeys in a bbox """
    tiles = mercantile.tiles(bbox[0], bbox[1], bbox[2], bbox[3], int(zoom))
    quadkeys = []
    for tile in tiles:
        quadkeys.append(mercantile.quadkey(tile))

    return quadkeys


def tuple_to_dict(t):
    """ Convert the results tuple to dict """
    return {"quadkey": t[0], "avg": t[1]}


def geojson_bounds(geojson):
    """
    Get the bounds of a geojson feature collection
    Based on https://github.com/Luqqk/geojson-bbox/blob/master/gbbox/geojson_bbox.py
    """

    # flatten the coordinates
    coords = list(flatten([f['geometry']['coordinates']
                  for f in geojson['features']]))

    return [min(coords[::2]), min(coords[1::2]),
            max(coords[::2]), max(coords[1::2])]


def flatten(value):
    """
    Helper function to flatten coordinates
    """
    for val in value:
        if isinstance(val, list):
            for subval in flatten(val):
                yield subval
        else:
            yield val


def polygon_to_wkt(geojson):
    """
    Convert a geojson polygon to wkt
    """
    return f'SRID=4326;{shape(geojson).wkt}'
