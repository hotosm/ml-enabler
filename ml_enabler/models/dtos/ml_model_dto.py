from schematics import Model
from schematics.types import StringType, IntType, DateTimeType, ListType, FloatType


class MLModelDTO(Model):
    """ Describes JSON of an ML Model """

    model_id = IntType(serialized_name='modelId')
    created = DateTimeType()
    name = StringType(required=True)
    source = StringType(required=True)
    project_url = StringType(serialized_name='projectUrl')


class PredictionDTO(Model):
    """ Describes JSON of a set of predictions from a model """

    prediction_id = IntType(serialized_name='predictionsId')
    created = DateTimeType()
    model_id = IntType(serialized_name='modelId', required=True)
    version_id = IntType(serialized_name='versionId', required=True)
    version_string = StringType(serialized_name='versionString')
    docker_url = StringType(serialized_name='dockerUrl')
    bbox = ListType(FloatType, required=True)
    tile_zoom = IntType(serialized_name='tileZoom', required=True)

    """ Asset Status
        log_link - store a link to the AWS CloudWatch Console
        model_link - store a link to the S3 Location of the raw model
        docker_link - store a link to the container in ECR
        save_link - download the TFServing container
    """

    log_link = StringType(serialized_name='logLink')
    model_link = StringType(serialized_name='modelLink')
    docker_link = StringType(serialized_name='dockerLink')
    save_link = StringType(serialized_name='saveLink')


class MLModelVersionDTO(Model):
    """ Describes JSON of a ML model version """

    version_id = IntType(serialized_name='versionId')
    created = DateTimeType()
    model_id = IntType(serialized_name='modelId', required=True)
    version_major = IntType(serialized_name='versionMajor', required=True)
    version_minor = IntType(serialized_name='versionMinor', required=True)
    version_patch = IntType(serialized_name='versionPatch', required=True)
