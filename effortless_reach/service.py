from datetime import datetime

from decouple import config

from effortless_reach.models import Podcast, PodcastEpisode, Transcript, TranscriptRequest, TranscriptChunk, Summary, \
    KeyPoints
from transformer.transformers import summarize_podcast_section_summaries, summarize_podcast_section_key_points, \
    podcast_transcript_to_key_points, podcast_transcript_to_summary

from whisper.whisper import Whisper
from search.tasks import save_content_task
import logging

from langchain.text_splitter import NLTKTextSplitter

from open_ai.api import OpenAIAPI
import uuid

from pinecone_api.pinecone_api import PineconeAPI

logger = logging.getLogger(__name__)

def process_channel(channel, feed):
    podcast = Podcast()
    try:
        podcast.title = channel.title
        podcast.link = channel.link
        podcast.description = channel.description
        podcast.image = channel.image.href
    except:
        logger.error("Error while processing channel: %s", channel)
        logger.error("saving minimal info")
    podcast.rss_feed = feed
    podcast.save()
    return podcast

def process_entry(entry, podcast, generator):
    episode = PodcastEpisode()
    try:
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
        episode.image = entry.img
    except Exception as e:
        logger.error("Error while processing entry: %s", entry)
        logger.error(str(e))
        logger.error("saving minimal info")
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
        logger.info("Creating embeddings for podcast episode: %s", podcast_episode.title)
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
    logger.error("Splitting text into chunks")
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
        embeddings = openai_api.embeddings(transcript_chunk.text, source='ChooseYourAlgorithm', parent_id=parent_id)
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
        'environment': config('ENVIRONMENT', default='development'),
        'podcast': transcript_chunk.transcript.episode.podcast.title,
        'episode': transcript_chunk.transcript.episode.title,
        'content_source': 'transcript'
    }
    pinecone.upsert([(str(transcript_chunk.chunk_id), transcript_chunk.embeddings, metadata)])
    transcript_chunk.embeddings_saved = True
    transcript_chunk.save()


def divide_chunks(l, n):
    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]
def summarize(podcast_episode_id):
    episode_summary = Summary.objects.filter(episode_id=podcast_episode_id).first()
    if episode_summary:
        return episode_summary
    openai = OpenAIAPI()
    summary_chunks = []
    chunks = TranscriptChunk.objects.filter(transcript__episode__id=podcast_episode_id).all()
    if not chunks:
        logger.info("No transcript chunks found. Creating them now...")
        create_embeddings_for_podcast_episode(podcast_episode_id)
        chunks = TranscriptChunk.objects.filter(transcript__episode__id=podcast_episode_id).all()
    parent_id = uuid.uuid4()

    for chunk in chunks:
        summary_prompt = podcast_transcript_to_summary(chunk)

        summary = openai.complete(summary_prompt, source="ChooseYourAlgorithm", parent_id=parent_id,
                                  stop_tokens=['The summary:'])
        if summary:
            summary_chunks.append(summary)
        else:
            logger.warning(f"Summary for chunk {chunk.id} is empty")



    logger.info(summarize_podcast_section_summaries(summary_chunks))
    intermediate_summaries = []
    for intermediate_chunk in divide_chunks(summary_chunks, 10):
        intermediate_summary = openai.complete(summarize_podcast_section_summaries(intermediate_chunk), source="ChooseYourAlgorithm",
                              parent_id=parent_id, )
        intermediate_summaries.append(intermediate_summary)
    summary = openai.complete(summarize_podcast_section_summaries(intermediate_summaries),
                                           source="ChooseYourAlgorithm",
                                           parent_id=parent_id, )
    episode_summary = Summary.objects.create(episode_id=podcast_episode_id, text=summary)
    return episode_summary

def get_keypoints(podcast_episode_id):
    episode_keypoints = KeyPoints.objects.filter(episode_id=podcast_episode_id).first()
    if episode_keypoints:
        return episode_keypoints
    openai = OpenAIAPI()
    key_points_chunks = []
    chunks = TranscriptChunk.objects.filter(transcript__episode__id=podcast_episode_id).all()
    if not chunks:
        logger.info("No chunks found. Creating embeddings for podcast episode")
        create_embeddings_for_podcast_episode(podcast_episode_id)
        chunks = TranscriptChunk.objects.filter(transcript__episode__id=podcast_episode_id).all()
    parent_id = uuid.uuid4()
    for chunk in chunks:
        key_points_prompt = podcast_transcript_to_key_points(chunk)
        key_points = openai.complete(key_points_prompt, source="ChooseYourAlgorithm", parent_id=parent_id,  stop_tokens=['The key points:'])
        if key_points:
            key_points_chunks.append(key_points)
        else:
            logger.warning(f"Got no key points for chunk {chunk.text}")
    intermediate_key_points = []
    for intermediate_chunk in divide_chunks(key_points_chunks, 10):
        intermediate_key_point = openai.complete(summarize_podcast_section_key_points(intermediate_chunk), source="ChooseYourAlgorithm",
                                     parent_id=parent_id, )
        intermediate_key_points.append(intermediate_key_point)
    key_points = openai.complete(summarize_podcast_section_key_points(intermediate_key_points), source="ChooseYourAlgorithm",
                             parent_id=parent_id, )
    episode_keypoints = KeyPoints.objects.create(episode_id=podcast_episode_id, text=key_points)
    return episode_keypoints

