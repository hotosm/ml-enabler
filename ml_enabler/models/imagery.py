from ml_enabler import db
from ml_enabler.models.dtos.ml_model_dto import ImageryDTO

class Imagery(db.Model):
    """ Store an imagery source for a given model """
    __tablename__ = 'imagery'

    id = db.Column(db.Integer, primary_key=True)

    model_id = db.Column(
        db.BigInteger,
        db.ForeignKey('ml_models.id', name='fk_models'),
        nullable=False
    )

    name = db.Column(db.String, nullable=False)
    url =  db.Column(db.String, nullable=False)
    fmt = db.Column(db.String, nullable=False)

    def create(self, model_id: int, imagery: dict):
        """ Creates and saves the current model to the DB """

        self.model_id = model_id
        self.name = imagery.get("name")
        self.url = imagery.get("url")

        db.session.add(self)
        db.session.commit()

        return self

    def as_dto(self):
        imagery_dto = ImageryDTO()
        imagery_dto.id = self.id
        imagery_dto.model_id = self.model_id
        imagery_dto.name = self.name
        imagery_dto.url = self.url

        return imagery_dto

    def get(imagery_id: int):
        query = db.session.query(
            Imagery.id,
            Imagery.name,
            Imagery.url,
            Imagery.model_id
        ).filter(Imagery.id == imagery_id)

        return Imagery.query.get(imagery_id)

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    def list(model_id: int):
        query = db.session.query(
            Imagery.id,
            Imagery.name,
            Imagery.url
        ).filter(Imagery.model_id == model_id)

        imagery = []
        for img in query.all():
            imagery.append({
                "id": img[0],
                "name": img[1],
                "url": img[2]
            })

        return imagery

    def update(self, update: dict):
        if update.get("name") is not None:
            self.name = update["name"]
        if update.get("url") is not None:
            self.url = update["url"]

        db.session.commit()

