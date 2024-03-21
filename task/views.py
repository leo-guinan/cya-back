import json
import uuid

from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from task.models import Task
from task.service import identify_tasks, generateTasksFromPlan


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def add(request):
    body = json.loads(request.body)
    message = body['message']
    user_id = body['user_id']

    # identify task if needed.
    tasks = identify_tasks(message)
    task_models = []
    for task in tasks:
        print(task)
        task_model = Task()
        task_model.task = task['name']
        task_model.taskFor = task['taskFor']
        task_model.details = task['details']
        task_model.uuid = str(uuid.uuid4())
        task_model.user_id = user_id
        task_model.save()
        task_models.append(task_model)
    return Response({'status': 'success'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def list(request):
    body = json.loads(request.body)
    user_id = body['user_id']

    # identify task if needed.
    tasks = Task.objects.filter(user_id=user_id, complete=False).all()
    task_models = []
    for task in tasks:
        task_models.append({
            "name": task.task,
            "description": task.description,
            "taskFor": task.taskFor,
            "id": task.id,
            "priority": task.priority,
            "uuid": task.uuid,
        })
    return Response({'tasks': task_models})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def prioritize(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    task_priorities = body['task_priorities']
    print(json.dumps(task_priorities, indent=4))
    for task_priority in task_priorities:
        print(task_priority['task'])
        task_object = task_priority['task']
        # uuid indicates task originated from external source
        if 'uuid' in task_object:
            task = Task.objects.filter(uuid=task_object['uuid'], user_id=user_id).first()
            if not task:
                task = Task.objects.filter(id=task_object['id'], user_id=user_id).first()
        else:
            task = Task.objects.filter(id=task_object['id'], user_id=user_id).first()
        if not task:
            task = Task()
            task.user_id = user_id
            task.task = task_priority['task']['name']
            task.uuid = task_priority['task']['uuid']
            # need to make these the same
            task.description = task_priority['task']['description']


        task.priority = task_priority['priority']
        task.save()

    return Response({'status': "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def complete(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    task_id = body['task_id']
    task = Task.objects.get(id=task_id, user_id=user_id)
    if not task:
        return Response({'status': "error"})

    task.complete = True
    task.completedAt = timezone.now()
    task.save()
    return Response({'status': "success"})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def generate(request):
    body = json.loads(request.body)
    plan = body['plan']

    planned_tasks = generateTasksFromPlan(plan)

    return Response({'tasks': planned_tasks})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([])
@csrf_exempt
def get(request):
    body = json.loads(request.body)
    user_id = body['user_id']
    task_id = body['task_id']
    external_uuid = body['uuid']

    # identify task if needed.
    task = Task.objects.filter(user_id=user_id, complete=False, id=task_id).first()
    if not task.uuid:
        task.uuid = external_uuid
        task.save()
    task_model = {
            "name": task.task,
            "description": task.description,
            "taskFor": task.taskFor,
            "id": task.id,
            "priority": task.priority,
            "uuid": task.uuid,
        }
    return Response({'task': task_model})