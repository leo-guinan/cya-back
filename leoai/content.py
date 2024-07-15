import uuid
from operator import itemgetter

import chromadb
from decouple import config
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains.retrieval import create_retrieval_chain
from langchain.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from chromadb.utils import embedding_functions
from leoai.rag import reciprocal_rank_fusion
from submind.llms.submind import SubmindModelFactory


def find_content_for_query(query: str):
    answer, youtube_content = get_youtube_content(query)
    return answer, youtube_content


def get_youtube_content(query: str):
    chroma_client = chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)

    embedding_function = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                            model_name="text-embedding-3-small")

    default_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=config('OPENAI_API_KEY'),  model_name="text-embedding-3-small")
    collection = chroma_client.get_collection(name="ideasupplychain_yt", embedding_function=default_ef)

    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    print(f"Number of results: {len(results['ids'])}")
    prepped_results = []
    existing_ids = set()

    for index, result in enumerate(results['ids'][0]):
        if results['metadatas'][0][index]['videoId'] in existing_ids:
            continue
        existing_ids.add(results['metadatas'][0][index]['videoId'])
        metadata = results['metadatas'][0][index]
        print(f"Title: {metadata['title']}")
        text = results['documents'][0][index]
        print(f"Text: {text}")
        distance = results['distances'][0][index]
        print(f"Distance: {distance}")
        prepped_results.append({
            "metadata": metadata,
            "text": text,
            "distance": distance
        })
    print(f"Number of prepped results: {len(prepped_results)}")

    SYSTEM_TEMPLATE = """
    Answer the user's question based on the below context. 
    If the context doesn't contain any relevant information to the question, don't make something up and just say "I don't know":

    <context>
    {context}
    </context>
    
    Question: {question}
    """

    model = SubmindModelFactory.get_model('Idea Supply Chain Youtube', "content_lookup")
    prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
    chain = prompt | model | StrOutputParser()

    context = "\n".join(map(lambda x: x['text'], prepped_results))
    print("Context: ", context)
    response = chain.invoke({"context": context, "question": query})

    return response, prepped_results


