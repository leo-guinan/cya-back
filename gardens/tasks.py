from backend.celery import app
from gardens.models import ContentFeed, Content
from rss.service import parse_feed
import dateutil.parser
@app.task(name="fetch_content")
def fetch_content_for_feed(feed_id):
    feed = ContentFeed.objects.get(id=feed_id)
    entries = parse_feed(feed.source.feed_location)
    for entry in entries:
        content = Content()
        content.owner = feed.owner
        content.url = find_best_link(entry['links'])
        if entry['image']:
            content.image = entry['image']['href']
        elif entry['media_thumbnail']:
            content.image = entry['media_thumbnail'][0]['url']
        content.feed = feed
        content.title = entry['title']
        content.summary = entry['summary']
        content.published = dateutil.parser.parse(entry['published'])
        content.save()

def find_best_link(links):
    best_link = None
    for link in links:
        if link['type'] in [ 'audio/x-m4a', 'audio/mpeg' ]:
            best_link = link['href']
    if best_link:
        return best_link
    return links[0]['href']