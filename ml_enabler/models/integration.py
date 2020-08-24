from ml_enabler import db
from ml_enabler.models.dtos.ml_model_dto import IntegrationDTO

class Integration(db.Model):
    """ Store an integration for a given model """
    __tablename__ = 'integration'

    id = db.Column(db.Integer, primary_key=True)

    model_id = db.Column(
        db.BigInteger,
        db.ForeignKey('ml_models.id', name='fk_models'),
        nullable=False
    )

    integration = db.Column(db.String, nullable=False)
    name = db.Column(db.String, nullable=False)
    url =  db.Column(db.String, nullable=False)
    auth = db.Column(db.String, nullable=True)

    def create(self, model_id: int, integration: dict):
        """ Creates and saves the current model to the DB """

        self.model_id = model_id
        self.integration = integration.get("integration")
        self.auth = integration.get("auth")
        self.name = integration.get("name")
        self.url = integration.get("url")

        db.session.add(self)
        db.session.commit()

        return self

    def as_dto(self):
        integration_dto = IntegrationDTO()
        integration_dto.id = self.id
        integration_dto.model_id = self.model_id
        integration_dto.integration = self.integration
        integration_dto.name = self.name
        integration_dto.url = self.url

        return integration_dto

    def get(integration_id: int):
        query = db.session.query(
            Integration.id,
            Integration.name,
            Integration.integration,
            Integration.url,
            Integration.model_id
        ).filter(Integration.id == integration_id)

        return Integration.query.get(integration_id)

    def get_secrets(integration_id: int):
        query = db.session.query(
            Integration.id,
            Integration.auth,
            Integration.name,
            Integration.integration,
            Integration.url,
            Integration.model_id
        ).filter(Integration.id == integration_id)

        return Integration.query.get(integration_id)

    def delete(self):
        """ Deletes the current model from the DB """
        db.session.delete(self)
        db.session.commit()

    def list(model_id: int):
        query = db.session.query(
            Integration.id,
            Integration.name,
            Integration.url,
            Integration.integration
        ).filter(Integration.model_id == model_id)

        integrations = []
        for integration in query.all():
            integrations.append({
                "id": integration[0],
                "name": integration[1],
                "url": integration[2],
                "integration": integration[3]
            })

        return integrations

    def update(self, update: dict):
        if update.get("name") is not None:
            self.name = update["name"]
        if update.get("auth") is not None:
            self.auth = update["auth"]
        if update.get("url") is not None:
            self.url = update["url"]

        db.session.commit()

