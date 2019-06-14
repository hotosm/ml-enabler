from ml_enabler.models.utils import geojson_bounds, polygon_to_wkt
from ml_enabler.tests.base import BaseTestCase


class UtilsTest(BaseTestCase):
    def test_geojson_bounds(self):
        # flake8: noqa
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        25.169677734375,
                        54.635697306063854
                        ],
                        [
                        25.32623291015625,
                        54.635697306063854
                        ],
                        [
                        25.32623291015625,
                        54.71034215072395
                        ],
                        [
                        25.169677734375,
                        54.71034215072395
                        ],
                        [
                        25.169677734375,
                        54.635697306063854
                        ]
                    ]
                    ]
                }
                },
                {
                "type": "Feature",
                "properties": {},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                    [
                        [
                        25.2410888671875,
                        54.5162988390112
                        ],
                        [
                        25.38116455078125,
                        54.5162988390112
                        ],
                        [
                        25.38116455078125,
                        54.5800215520618
                        ],
                        [
                        25.2410888671875,
                        54.5800215520618
                        ],
                        [
                        25.2410888671875,
                        54.5162988390112
                        ]
                    ]
                    ]
                }
                }
            ]
        }

        bounds = geojson_bounds(geojson)
        assert(bounds == [25.169677734375, 54.5162988390112, 25.38116455078125, 54.71034215072395])

    
    def test_polygon_to_wkt(self):
        geojson = {
            "type": "Polygon",
            "coordinates": [
                [
                    [
                    25.169677734375,
                    54.635697306063854
                    ],
                    [
                    25.32623291015625,
                    54.635697306063854
                    ],
                    [
                    25.32623291015625,
                    54.71034215072395
                    ],
                    [
                    25.169677734375,
                    54.71034215072395
                    ],
                    [
                    25.169677734375,
                    54.635697306063854
                    ]
                ]
            ]
        }

        wkt = polygon_to_wkt(geojson)
        assert(wkt == 'SRID=4326;POLYGON ((25.169677734375 54.63569730606385, 25.32623291015625 54.63569730606385, 25.32623291015625 54.71034215072395, 25.169677734375 54.71034215072395, 25.169677734375 54.63569730606385))')