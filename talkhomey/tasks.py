from backend.celery import app
from talkhomey.models import Resource




def process(resource: Resource):
    # ... do something with the url
    return resource

@app.task(name="talkhomey.process_resource")
def process_resource(resource_id: int):
    # ... do something with the url
    resource = Resource.objects.get(id=resource_id)
    result = process(resource)
    return resource_id