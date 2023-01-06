from backend.celery import app
from client.models import ClientAccount
from search.service import save_item

@app.task(name="search.save_content")
def save_content_task(text, title, description, link, content_type, creator_id):
    creator = ClientAccount.objects.filter(id=creator_id).first()
    save_item(text, title, description, link, content_type, creator)