from datetime import datetime

from effortless_reach.models import Podcast, PodcastEpisode, Transcript, TranscriptRequest, TranscriptChunk

from whisper.whisper import Whisper
from search.tasks import save_content_task
import logging

from langchain.text_splitter import NLTKTextSplitter

from open_ai.api import OpenAIAPI
import uuid

from pinecone_api.pinecone_api import PineconeAPI
from search.models import ContentChunk

logger = logging.getLogger(__name__)

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
    try:
        episode.published_at = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %z")
    except ValueError:
        episode.published_at = datetime.strptime(entry.published, "%a, %d %b %Y %H:%M:%S %Z")

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

    if transcript and transcript.text:
        chunk_ids = split(transcript)
        for chunk_id in chunk_ids:
            get_embeddings(chunk_id)
            save_embeddings(chunk_id)




def split(transcript):
    # split text into chunks
    text = transcript.text
    splitter = NLTKTextSplitter(chunk_size=500)
    chunks = splitter.split_text(text)
    transcript_chunks = []

    for chunk in chunks:
        logger.debug(f"Saving chunk with size {len(chunk)}")
        if len(chunk) > 500:
            logger.debug(f"Chunk size is too big. Splitting again")
            sub_chunks = splitter.split_text(chunk)
            for sub_chunk in sub_chunks:
                transcript_chunk = TranscriptChunk.objects.create(transcript=transcript, text=sub_chunk, chunk_id=uuid.uuid4())
                transcript_chunks.append(transcript_chunk.id)
        else:
            transcript_chunk = TranscriptChunk.objects.create(transcript=transcript, text=chunk,
                                                              chunk_id=uuid.uuid4())
            transcript_chunks.append(transcript_chunk.id)
    return transcript_chunks


def get_embeddings(transcript_chunk_id):
    try:
        openai_api = OpenAIAPI()
        parent_id = uuid.uuid4()
        transcript_chunk = TranscriptChunk.objects.filter(id=transcript_chunk_id).first()
        embeddings = openai_api.embeddings(transcript_chunk.text, source='effortless_reach', parent_id=parent_id)
        transcript_chunk.embeddings = embeddings
        transcript_chunk.save()
    except Exception as e:
        # maybe we should retry?
        logger.error("Error while getting embeddings for transcript chunk: %s", e)
    # return embeddings
    return transcript_chunk_id

def save_embeddings(transcript_chunk_id):
    transcript_chunk = TranscriptChunk.objects.filter(id=transcript_chunk_id).first()
    pinecone = PineconeAPI()
    metadata = {
        'podcast': transcript_chunk.transcript.episode.podcast.title,
        'episode': transcript_chunk.transcript.episode.title,
    }
    pinecone.upsert([(str(transcript_chunk.chunk_id), transcript_chunk.embeddings, metadata)])
    transcript_chunk.embeddings_saved = True
    transcript_chunk.save()
