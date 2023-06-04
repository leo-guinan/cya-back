from backend.celery import app
from chat.models import ClientApp
from crawler.service import crawl
from decisions.models import MetaSearchEngine


@app.task(name="crawler.crawl_website")
def crawl_website(url: str, client_app_id: int):
    # ... do something with the url
    client_app = ClientApp.objects.get(id=client_app_id)
    result = crawl(url, client_app)
    return url


