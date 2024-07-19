from typing import Tuple, List, Dict

import chromadb
from chromadb.utils import embedding_functions
from decouple import config
from langchain.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from submind.llms.submind import SubmindModelFactory


def get_chroma_client():
    return chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)


def get_embedding_function():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=config('OPENAI_API_KEY'),
        model_name="text-embedding-3-small"
    )


def query_collection(collection_name: str, query: str, n_results: int = 10) -> List[Dict]:
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


def get_answer_from_context(context: str, query: str, model_name: str) -> str:
    print(f"Using context: {context}")
    SYSTEM_TEMPLATE = """
    Answer the user's question based on the below context. 
    If the context doesn't contain any relevant information to the question, don't make something up and just say "I don't know":

    <context>
    {context}
    </context>

    Question: {question}
    """

    model = SubmindModelFactory.get_model(model_name, "content_lookup")
    prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
    chain = prompt | model | StrOutputParser()

    return chain.invoke({"context": context, "question": query})


def get_content_and_answer(collection_name: str, query: str, model_name: str) -> Tuple[str, List[Dict]]:
    content = query_collection(collection_name, query)
    context = "\n".join(map(lambda x: x['text'], content))
    answer = get_answer_from_context(context, query, model_name)
    return answer, content


def find_ev_content(query: str) -> Tuple[str, List[Dict]]:
    answer, content = get_content_and_answer("evyoutube", query, "Ev Chapman Youtube")
    context = "\n".join(map(lambda x: x['text'], content))
    return context, content



def get_youtube_content(query: str) -> Tuple[str, List[Dict]]:
    return get_content_and_answer("ideasupplychain_yt", query, "Idea Supply Chain Youtube")


def get_substack_content(query: str) -> Tuple[str, List[Dict]]:
    return get_content_and_answer("engineering_generosity", query, "Idea Supply Chain Youtube")


def get_blog_content(query: str) -> Tuple[str, List[Dict]]:
    return get_content_and_answer("ideasupplychain_blog", query, "Idea Supply Chain Youtube")


def combine_content(query: str, content_list: List[List[Dict]]) -> Tuple[str, List[Dict]]:
    combined_content = [item for sublist in content_list for item in sublist]
    combined_content.sort(key=lambda x: x['distance'])
    top_content = combined_content[:3]

    context = "\n".join(map(lambda x: x['text'], top_content))
    answer = get_answer_from_context(context, query, "Idea Supply Chain Youtube")

    return context, top_content


def find_content_for_query(query: str) -> Tuple[str, List[Dict]]:
    yt_answer, youtube_content = get_youtube_content(query)
    ss_answer, substack_content = get_substack_content(query)
    blog_answer, blog_content = get_blog_content(query)

    return combine_content(query, [youtube_content, substack_content, blog_content])
