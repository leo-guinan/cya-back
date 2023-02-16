import logging
import uuid

from langchain.text_splitter import NLTKTextSplitter

from effortless_reach.models import TranscriptChunk
from open_ai.api import OpenAIAPI
from pinecone_api.pinecone_api import PineconeAPI
from search.models import ContentChunk

logger = logging.getLogger(__name__)


def split(content):
    # split text into chunks
    text = content.fulltext
    splitter = NLTKTextSplitter(chunk_size=500)
    chunks = splitter.split_text(text)
    content_chunks = []

    for chunk in chunks:
        logger.debug(f"Saving chunk with size {len(chunk)}")
        if len(chunk) > 500:
            logger.debug(f"Chunk size is too big. Splitting again")
            sub_chunks = splitter.split_text(chunk)
            for sub_chunk in sub_chunks:
                content_chunk = ContentChunk.objects.create(content=content, text=sub_chunk, chunk_id=uuid.uuid4())
                content_chunks.append(content_chunk.id)
        else:
            content_chunk = ContentChunk.objects.create(content=content, text=chunk, chunk_id=uuid.uuid4())
            content_chunks.append(content_chunk.id)
    return content_chunks


def get_embeddings(content_chunk_id):
    try:
        openai_api = OpenAIAPI()
        parent_id = uuid.uuid4()
        content_chunk = ContentChunk.objects.filter(id=content_chunk_id).first()
        embeddings = openai_api.embeddings(content_chunk.text, source='search', parent_id=parent_id)
        content_chunk.embeddings = embeddings
        content_chunk.save()
    except Exception as e:
        # maybe we should retry?
        logger.error("Error while getting embeddings for content chunk: %s", e)
    # return embeddings
    return content_chunk_id


def query_topics(topics,  metadata=None):
    pinecone = PineconeAPI()
    results = pinecone.search(query_vector=topics, k=10, metadata=metadata)
    result = results.matches[0]
    chunk = TranscriptChunk.objects.filter(chunk_id=result.id).first()
    return chunk.content.title, chunk.content.link, chunk.content.description, chunk.text, chunk.content.creator.email


def search(query):
    openai = OpenAIAPI()
    topic_embeddings = openai.embeddings(query, source="search")
    return query_topics(topic_embeddings)


def curated(query, curator):
    openai = OpenAIAPI()
    podcasts = [podcast.title for podcast in curator.podcasts.all()]
    episodes = [episode.title for episode in curator.podcast_episodes.all()]
    metadata = {
        "$or": [
            {"podcast": {"$in": podcasts}},
            {"episode": {"$in": episodes}}
        ]
    }

    topic_embeddings = openai.embeddings(query, source="search")
    return query_topics(topic_embeddings, metadata=metadata)


def save_embeddings(content_chunk_id, email, content_type):
    content_chunk = ContentChunk.objects.filter(id=content_chunk_id).first()
    pinecone = PineconeAPI()
    pinecone.upsert([(str(content_chunk.chunk_id), content_chunk.embeddings, {"author": email, "type": content_type})])
    content_chunk.embeddings_saved = True
    content_chunk.save()
