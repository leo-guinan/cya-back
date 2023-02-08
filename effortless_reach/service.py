from datetime import datetime

from effortless_reach.models import Podcast, PodcastEpisode, Transcript, TranscriptRequest
from search.models import Content

from whisper.whisper import Whisper
from search.tasks import save_content_task

def process_channel(channel, feed):
    podcast = Podcast()
    podcast.title = channel.title
    podcast.link = channel.link
    podcast.description = channel.description
    podcast.rss_feed = feed
    podcast.save()
    return podcast

def process_entry(entry, podcast, generator):
    episode = PodcastEpisode()
    episode.title = entry.title
    if 'Transistor' in generator:
        episode.link = entry.link
    else:
        episode.link = entry.links[0].href
    for link in entry.links:
        if link.type == "audio/mpeg":
            episode.download_link = link.href
            break
    episode.description = entry.description
    episode.published_at = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
    episode.podcast = podcast
    episode.save()
    transcript_request = TranscriptRequest()
    transcript_request.podcast_episode = episode
    transcript_request.save()
    return episode

def transcribe_episode(episode_id):
    podcast_episode = PodcastEpisode.objects.get(id=episode_id)
    transcript = Transcript.objects.filter(episode=podcast_episode).first()
    transcript_request = TranscriptRequest.objects.filter(podcast_episode=podcast_episode).first()
    if transcript is None:
        try:
            whisper = Whisper()
            transcript = Transcript()
            transcript.episode = podcast_episode
            transcript.save()
            whisper.transcribe_podcast(transcript.id)
            transcript_request.status = TranscriptRequest.RequestStatus.COMPLETED
            transcript_request.save()
        except Exception as e:
            transcript_request.error = str(e)
            transcript_request.status = TranscriptRequest.RequestStatus.FAILED
            transcript_request.save()

def create_embeddings_for_podcast_episode(episode_id):
    podcast_episode = PodcastEpisode.objects.get(id=episode_id)
    transcript = Transcript.objects.filter(episode=podcast_episode).first()

    if transcript is not None:
        content = Content()
        content.creator = podcast_episode.podcast.rss_feed.owner
        content.type = "podcast"
        content.fulltext = transcript.text
        content.title = podcast_episode.title
        content.description = podcast_episode.description
        content.link = podcast_episode.link
        content.save()
        save_content_task.delay(content.id)
