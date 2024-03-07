import json
import uuid

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

from task.models import Task
from task.service import identify_tasks


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

