from backend.celery import app
from embeddings.documents import save_document
from spark.manage import add_rss_feed


@app.task("spark.process_rss_feed")
def process_rss_feed(title, url):
    link = add_rss_feed(url, title)

    for child in link.children.all():
        save_document(child.fulltext, "spark")

