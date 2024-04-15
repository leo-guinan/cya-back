import json
import sys
import uuid

import requests
from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
from langchain_pinecone import PineconeVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone

from podcast.models import Podcast, PodcastEpisode, PodcastEpisodeSnippet


def look_for_podcast_episodes(query):
    """
    Look for podcast episodes
    """
    pc = Pinecone(api_key=config("PINECONE_API_KEY"))

    embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                  openai_api_base=config('OPENAI_API_BASE'),
                                  headers={
                                      "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                  })
    index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
    vectorstore = PineconeVectorStore(index, embeddings, "text")
    text_splitter = SemanticChunker(embeddings)
    backup_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )
    podscan_host = config("PODSCAN_HOST")
    podscan_api_key = config("PODSCAN_API_KEY")
    podscan_search = f'{podscan_host}/episodes/search?query={query}'
    headers = {
        "Authorization": f"Bearer {podscan_api_key}"
    }
    response = requests.get(podscan_search, headers=headers)
    episodes = response.json()

    found = []
    print(f"Found {len(episodes['episodes'])} episodes")

    for episode in episodes['episodes']:
        # if podcast episode is already in the database, skip it.
        if not episode['episode_guid']:
            existing_episode = PodcastEpisode.objects.filter(name=episode['episode_title'], podcast__external_id=episode['podcast']['podcast_id']).first()
        else:
            existing_episode = PodcastEpisode.objects.filter(transcript_guid=episode['episode_guid']).first()
        if existing_episode:
            found.append(existing_episode)
            continue

        existing_podcast = Podcast.objects.filter(external_id=episode['podcast']['podcast_id']).first()
        if not existing_podcast:
            existing_podcast = Podcast.objects.create(
                name=episode['podcast']['podcast_name'],
                external_id=episode['podcast']['podcast_id'],
                podcast_url=episode['podcast']['podcast_url']
            )

        existing_episode = PodcastEpisode.objects.create(
            name=episode['episode_title'],
            duration=episode['episode_duration'],
            podcast=existing_podcast,
            transcript_guid=episode['episode_guid'] if episode['episode_guid'] else str(uuid.uuid4()),
            transcript=episode['episode_transcript'],
            description=episode['episode_description'],
            episode_url=episode['episode_url'],
            episode_audio_url=episode['episode_audio_url'],
            embeddings_generated=False
        )

        chunks = text_splitter.split_text(existing_episode.transcript)
        metadatas = []
        ids = []
        chunks_to_save = []
        for chunk in chunks:
            id = str(uuid.uuid4())
            snippet = PodcastEpisodeSnippet.objects.create(
                podcast_episode=existing_episode,
                snippet=chunk,
                uuid=id
            )
            metadata = {
                "transcript_id": existing_episode.transcript_guid,
                "episode_id": existing_episode.id,
                "episode_name": existing_episode.name,
                "source_type": "podcast_episode",
                "snippet_id": snippet.id,
                "text": chunk
            }

            # test metadata size
            size = sys.getsizeof(json.dumps(metadata))

            if size > 40960:
                # remove the snippet, because it's too big
                snippet.delete()
                # need to split into smaller chunks
                smaller_chunks = backup_text_splitter.split_text(chunk)
                for smaller_chunk in smaller_chunks:
                    smaller_id = str(uuid.uuid4())
                    smaller_snippet = PodcastEpisodeSnippet.objects.create(
                        podcast_episode=existing_episode,
                        snippet=smaller_chunk,
                        uuid=smaller_id
                    )
                    smaller_metadata = {
                        "transcript_id": existing_episode.transcript_guid,
                        "episode_id": existing_episode.id,
                        "episode_name": existing_episode.name,
                        "source_type": "podcast_episode",
                        "snippet_id": smaller_snippet.id,
                        "text": smaller_chunk
                    }
                    metadatas.append(smaller_metadata)
                    ids.append(smaller_id)
                    chunks_to_save.append(smaller_chunk)
                continue
            else:
                chunks_to_save.append(chunk)
                metadatas.append(metadata)
                ids.append(id)

        vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=config('PINECONE_PODCAST_NAMESPACE'))

        found.append(existing_episode)

    return found
