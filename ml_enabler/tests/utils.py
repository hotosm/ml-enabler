from ml_enabler.tests.factories import MLModelFactory, MLModelVersionFactory, \
    PredictionFactory
from ml_enabler.models.ml_model import MLModel, Prediction
from ml_enabler import db


def create_prediction():
    ml_model = MLModelFactory()
    db.session.add(ml_model)
    db.session.commit()
    version = MLModelVersionFactory(model_id=ml_model.id)
    db.session.add(version)
    db.session.commit()

    # create the prediction
    prediction = PredictionFactory(model_id=ml_model.id,
                                   version_id=version.id)
    db.session.add(prediction)
    db.session.commit()

    return prediction
