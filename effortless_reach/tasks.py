from datetime import datetime

from backend.celery import app
from effortless_reach.models import RssFeed
from effortless_reach.service import process_channel, process_entry
from rss.service import parse_feed

@app.task(name="effortless_reach.process_rss_feed")
def process_rss_feed(feed_id):
    feed = RssFeed.objects.get(id=feed_id)
    parsed_feed = parse_feed(feed.url)
    channel = parsed_feed.channel
    podcast = process_channel(channel, feed)
    entries = parsed_feed.entries
    for entry in entries:
        process_entry(entry, podcast)
    feed.processed = True
    feed.processed_at = datetime.now()
    feed.save()

