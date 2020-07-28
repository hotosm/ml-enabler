from ml_enabler.models.utils import timestamp
from ml_enabler import db
from ml_enabler.models.dtos.ml_model_dto import TaskDTO
import sqlalchemy

class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    pred_id = db.Column(
        db.BigInteger,
        db.ForeignKey('predictions.id', name='fk_predictions'),
        nullable=False
    )
    type = db.Column(
        db.String,
        nullable=False
    )
    created = db.Column(db.DateTime, default=timestamp, nullable=False)
    batch_id = db.Column(db.String)

    def create(self, pred_id: int, type: str, batch_id: str):
        self.pred_id = pred_id
        self.type = type
        self.batch_id = batch_id

        db.session.add(self)
        db.session.commit()

        return self

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def get(task_id: int):
        query = db.session.query(
            Task.id,
            Task.pred_id,
            Task.type,
            Task.created,
            Task.batch_id
        ).filter(Task.id == task_id)

        return Task.query.get(task_id)

    def list(pred_id: int):
        query = db.session.query(
            Task.id,
            Task.pred_id,
            Task.type,
            Task.created,
            Task.batch_id
        ).filter(Task.pred_id == pred_id)

        return Task.query.all()

    def as_dto(self):
        task_dto = TaskDTO()
        task_dto.id = self.id
        task_dto.pred_id = self.pred_id
        task_dto.type = self.type
        task_dto.created = self.created
        task_dto.batch_id = self.batch_id

        return task_dto
