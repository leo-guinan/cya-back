import logging

from backend.celery import app
from embeddings.documents import save_document
from search.models import Fulltext, Link
from spark.manage import add_rss_feed
logger = logging.getLogger(__name__)

@app.task(name="spark.process_rss_feed")
def process_rss_feed(title, url):
    link = add_rss_feed(url, title)
    for child_link in link.children.all():
        logger.info("processing podcast episode")
        process_podcast.delay(child_link.id)


@app.task(name="spark.save_doc")
def save_doc(document_id):
    fulltext = Fulltext.objects.filter(id=document_id).first()
    if not fulltext:
        return
    save_document(fulltext, "spark")

@app.task(name="spark.process_podcast")
def process_podcast(link_id):
    link = Link.objects.filter(id=link_id).first()
    if not link or link.processed:
        return
    process_podcast(link)
    save_doc.delay(link.fulltext.id)