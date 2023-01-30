from datetime import datetime

from backend.celery import app
from effortless_reach.models import RssFeed, Podcast, PodcastEpisode, Transcript, TranscriptRequest
from effortless_reach.service import process_channel, process_entry, transcribe_episode
from rss.service import parse_feed

@app.task(name="effortless_reach.process_rss_feed")
def process_rss_feed(feed_id):
    feed = RssFeed.objects.get(id=feed_id)
    parsed_feed = parse_feed(feed.url)
    channel = parsed_feed.channel
    feed_generator = channel.generator if hasattr(channel, 'generator') else ''

    podcast = process_channel(channel, feed)
    entries = parsed_feed.entries
    for entry in entries:
        process_entry(entry, podcast, feed_generator)
    feed.processed = True
    feed.processed_at = datetime.now()
    feed.save()

@app.task(name="effortless_reach.transcribe_podcast")
def transcribe_podcast(podcast_episode_id):
    transcribe_episode(podcast_episode_id)


@app.task(name="effortless_reach.transcribe_all_podcasts")
def transcribe_all_podcasts():
    transcription_requests = TranscriptRequest.objects.filter(status=TranscriptRequest.RequestStatus.PENDING).all()
    for request in transcription_requests:
        transcribe_podcast.apply_async([request.podcast_episode.id,], queue='bot' )
        request.status = TranscriptRequest.RequestStatus.PROCESSING
        request.save()
