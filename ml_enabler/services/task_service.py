from ml_enabler.models.task import Task
from ml_enabler import db

class TaskService():
    @staticmethod
    def create(payload: dict) -> int:
        task = Task()

        task.create(
            payload.get('pred_id'),
            payload.get('type'),
            payload.get('batch_id')
        )

        return task.id

    @staticmethod
    def delete(task_id: int):
        task = Task.get(task_id)
        task.delete()

    def list(pred_id: int, task_type: str):
        rawtasks = Task.list(pred_id, task_type)

        tasks = []
        if (rawtasks):
            for task in rawtasks:
                tasks.append(task.as_dto().to_primitive())

            return {
                'pred_id': pred_id,
                'tasks': tasks
            }
        else:
            return {
                'pred_id': pred_id,
                'tasks': []
            }

