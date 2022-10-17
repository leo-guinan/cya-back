from backend.celery import app
from gardens.models import ContentFeed, Content
from rss.service import parse_feed

@app.task(name="fetch_content")
def fetch_content_for_feed(feed_id):
    feed = ContentFeed.objects.get(id=feed_id)
    entries = parse_feed(feed.source.feed_location)
    for entry in entries:
        content = Content()
        content.owner = feed.owner
        content.url = entry['link']
        content.feed = feed
        content.title = entry['title']
        content.summary = entry['summary']
        content.published = entry['published']
        content.save()

