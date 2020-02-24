# ML Enabler API v1

The API endpoints are documented in detail via [Swagger](/docs). The following are the available endpoints.

## GET /
Health check endpoint

## GET v1/docs
See documentation

## GET v1/model/all
Get all models

## POST v1/model

Subscribe a model with the ML Enabler. The following is an example payload.

```
{
    "name": "looking-glass",
    "source": "developmentseed",
    "dockerhubUrl": "https://hub.docker.com/r/developmentseed/looking-glass"
}

Response is the ID of the model

```

## GET v1/model/<int:model_id>

Fetch information about a model with the `id`


## PUT v1/model/<int:model_id>

Modify model information. The payload looks like:

```
{
    "name": "non-looking-glass",
    "source": "developmentseed",
    "dockerhubUrl": "https://hub.docker.com/r/developmentseed/looking-glass"
}
```

## DELETE v1/model/<int:model_id>

Delete the model

## POST v1/model/<int:model_id>/prediction

Create predictions of a model. The payload looks like:

```
{
    "modelId": 1,
    "version": "2.0.0",
    "bbox": [10.013795,53.5225,10.048885,53.540843],
    "tileZoom": 18
}
```

## GET v1/model/<int:model_id>/prediction/all

Fetch all predictions of the given model. The response is an array of prediction objects.


## GET v1/model/<int:model_id>/prediction

Fetch predictions of a model within the supplied bbox. For example, `model/1/prediction?bbox=5.53,47.23,15.38,54.96`, will fetch all prediction within that bbox. The response is an array of prediction objects.


## POST v1/model/prediction/<int:prediction_id>/tiles

Submit a JSON of tiles ideally from ml-enabler-cli. The payload looks like:

```
{
  "predictionId": prediction_id,
  "predictions": [
    {
    "quadkey": "120201312023333233",
    "predictions": {"ml_prediction": 65536.0},
    "centroid": "SRID=4326;POINT (10.01266479492188 53.54030739150021)",
    "prediction_id": prediction_id
    }
  ]
}

```

## GET v1/model/<int:id>/tiles

Fetch prediction tiles for the model within the give bbox. The aggregation is dependent on the zoom level. For example: `/model/1/tiles?bbox=10.013795,53.5225,10.048885,53.540843&zoom=14`, will fetch the prediction tiles in the bbox and return aggregated values at z14. This uses the latest prediction of the model.

The response looks like:

```
{
    "8": [
        {
            "quadkey": "12020131221002",
            "avg": 61365.1914893617
        },
        {
            "quadkey": "12020131221001",
            "avg": 63304.1379310345
        },
        {
            "quadkey": "12020131221000",
            "avg": 58488.0083333333
        },
        {
            "quadkey": "12020131220111",
            "avg": 54979.025
        },
        {
            "quadkey": "12020131202333",
            "avg": 65244.8
        },
        {
            "quadkey": "12020131203223",
            "avg": 65536
        },
        {
            "quadkey": "12020131221003",
            "avg": 47146.6857142857
        },
        {
            "quadkey": "12020131220113",
            "avg": 64469.4666666667
        },
        {
            "quadkey": "12020131203222",
            "avg": 64271.5625
        }
    ]
}
```

## POST v1/model/<int:id>/tiles/geojson

For a GeoJSON feature collection of polygons, get predictions for each polygon from the model. This uses the latest prediction of the model.

Example payload is:

```
{
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
              11.953125,
              51.18622962638683
            ],
            [
              12.689208984375,
              51.18622962638683
            ],
            [
              12.689208984375,
              51.49506473014368
            ],
            [
              11.953125,
              51.49506473014368
            ],
            [
              11.953125,
              51.18622962638683
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
              11.53564453125,
              51.59754765771458
            ],
            [
              12.5244140625,
              51.59754765771458
            ],
            [
              12.5244140625,
              51.890053935216926
            ],
            [
              11.53564453125,
              51.890053935216926
            ],
            [
              11.53564453125,
              51.59754765771458
            ]
          ]
        ]
      }
    }
  ]
}
```
