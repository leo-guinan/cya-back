from datetime import datetime

from effortless_reach.models import Podcast, PodcastEpisode


def process_channel(channel, feed):
    podcast = Podcast()
    podcast.title = channel.title
    podcast.link = channel.link
    podcast.description = channel.description
    podcast.rss_feed = feed
    podcast.save()
    return podcast

def process_entry(entry, podcast):
    episode = PodcastEpisode()
    episode.title = entry.title
    episode.link = entry.link
    for link in entry.links:
        if link.type == "audio/mpeg":
            episode.download_link = link.href
            break
    episode.description = entry.description
    episode.published_at = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
    episode.podcast = podcast
    episode.save()
    return episode