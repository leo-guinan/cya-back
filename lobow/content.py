from typing import List, Dict

import chromadb
from chromadb.utils import embedding_functions
from decouple import config


def get_chroma_client():
    return chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)


def get_embedding_function():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=config('OPENAI_API_KEY'),
        model_name="text-embedding-3-small"
    )


def query_collection(collection_name: str, query: str, n_results: int = 1) -> List[Dict]:
    chroma_client = get_chroma_client()
    embedding_function = get_embedding_function()
    collection = chroma_client.get_collection(name=collection_name, embedding_function=embedding_function)

    results = collection.query(query_texts=[query], n_results=n_results)

    prepped_results = []
    existing_ids = set()

    for index, result in enumerate(results['ids'][0]):
        metadata = results['metadatas'][0][index]
        id_key = 'videoId' if 'videoId' in metadata else 'title'

        if metadata[id_key] in existing_ids:
            continue

        existing_ids.add(metadata[id_key])
        prepped_results.append({
            "metadata": metadata,
            "text": results['documents'][0][index],
            "distance": results['distances'][0][index],
            "source": collection_name
        })

    return prepped_results

def get_content_from_youtube(query):
    return query_collection("lobowspark", query)
