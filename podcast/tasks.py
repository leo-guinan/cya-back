import uuid

from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone as PineconeVectorStore
from pinecone import Pinecone

from backend.celery import app
from podcast.models import PodcastQuery, PodcastEpisodeSnippet
from podcast.podscan import look_for_podcast_episodes


@app.task(name="podcast.tasks.search")
def search(query_id):
    """
    Look for podcast episodes
    """
    try:
        print("Starting search...")
        pc = Pinecone(api_key=config("PINECONE_API_KEY"))
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'),
                                      headers={
                                          "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                      })
        index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
        vectorstore = PineconeVectorStore(index, embeddings, "text")

        query = PodcastQuery.objects.get(id=query_id)

        found_episodes = look_for_podcast_episodes(query.query)
        matched_snippets = []

        for episode in found_episodes:
            # find relevant snippets
            matched = vectorstore.similarity_search_with_score(query.query, k=2, namespace=config('PINECONE_PODCAST_NAMESPACE'))
            for match in matched:
                snippet = PodcastEpisodeSnippet.objects.create(
                    podcast_episode=episode,
                    snippet=match[0].page_content,
                    score=match[1],
                    uuid=str(uuid.uuid4())
                )
                matched_snippets.append(snippet)

        query.podcast_episodes.add(*found_episodes)
        query.snippets.add(*matched_snippets)
        query.completed = True
        query.save()
    except Exception as e:
        query = PodcastQuery.objects.get(id=query_id)

        print(e)
        query.error = str(e)
        query.completed = True
        query.save()
        return


@app.task(name="podcast.tasks.detailed_search")
def detailed_search(query: str):
    """
    Look for podcast episodes
    """
    query = PodcastQuery.objects.create(query=query)

    try:
        pc = Pinecone(api_key=config("PINECONE_API_KEY"))
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'),
                                      headers={
                                          "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                      })
        index = pc.Index(config("BIPC_PINECONE_INDEX_NAME"), host=config("PINECONE_HOST"))
        vectorstore = PineconeVectorStore(index, embeddings, "text")




        found_episodes = look_for_podcast_episodes(query.query)
        print(f"Found {len(found_episodes)} episodes")
        matched_snippets = []
        # find potential episodes based on initial query. Then expand search to try to answer multiple questions.




        for episode in found_episodes:
            # find relevant snippets
            matched = vectorstore.similarity_search_with_score(query.query, k=2, namespace=config('PINECONE_PODCAST_NAMESPACE'))
            for match in matched:
                snippet = PodcastEpisodeSnippet.objects.create(
                    podcast_episode=episode,
                    snippet=match[0].page_content,
                    score=match[1],
                    uuid=str(uuid.uuid4())
                )
                matched_snippets.append(snippet)

        query.podcast_episodes.add(*found_episodes)
        query.snippets.add(*matched_snippets)
        query.completed = True
        query.save()
    except Exception as e:
        print(e)
        query.error = str(e)
        query.completed = True
        query.save()
        return
