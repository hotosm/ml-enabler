from ml_enabler.models.task import Task
from ml_enabler import db
from ml_enabler.models.utils import NotFound
import boto3

batch = boto3.client(
    service_name='batch',
    region_name='us-east-1',
    endpoint_url='https://batch.us-east-1.amazonaws.com'
)

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
        if task:
            task.delete()

            if task.batch_id:
                batch.cancel_job(
                    jobId=task.batch_id,
                    reason='User Requested'
                )

            return {
                'status': 'deleted'
            }
        else:
            raise NotFound

    @staticmethod
    def list(pred_id: int, task_type: str):
        rawtasks = Task.list(pred_id, task_type)

        if not rawtasks:
            raise NotFound

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

    @staticmethod
    def get(task_id: int):
        task = Task.get(task_id)

        if not task:
            raise NotFound

        task = task.as_dto().to_primitive()

        if task.get('batch_id') is not None:
            desc = batch.describe_jobs(
                jobs = [ task.get('batch_id') ]
            )

            if len(desc.get('jobs')) == 1:
                task['status'] = desc['jobs'][0].get('status')
                task['statusReason'] = desc['jobs'][0].get('statusReason')
            else:
                task['status'] = 'UNKNOWN'
                task['statusReason'] = 'AWS does not report this task'

        return task
