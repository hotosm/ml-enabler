from schematics import Model
from schematics.types import StringType, IntType, DateTimeType, ListType, FloatType, BooleanType


class MLModelDTO(Model):
    """ Describes JSON of an ML Model """

    model_id = IntType(serialized_name='modelId')
    created = DateTimeType()
    name = StringType(required=True)
    source = StringType(required=True)
    archived = BooleanType()
    project_url = StringType(serialized_name='projectUrl')

class PredictionDTO(Model):
    """ Describes JSON of a set of predictions from a model """

    prediction_id = IntType(serialized_name='predictionsId')
    created = DateTimeType()
    model_id = IntType(serialized_name='modelId', required=True)
    version = StringType(serialized_name='version', required=True)
    docker_url = StringType(serialized_name='dockerUrl')
    tile_zoom = IntType(serialized_name='tileZoom', required=True)
    inf_list = StringType(serialized_name='infList', required=True)
    inf_type = StringType(serialized_name='infType', required=True)
    inf_binary = BooleanType(serialized_name='infBinary', required=True)
    inf_supertile = BooleanType(serialized_name='infSupertile', required=True)

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

