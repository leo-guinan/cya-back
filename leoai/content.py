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

def find_ev_content(query: str):
    chroma_client = chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)

    embedding_function = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                          model_name="text-embedding-3-small")

    default_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=config('OPENAI_API_KEY'),
                                                             model_name="text-embedding-3-small")
    collection = chroma_client.get_collection(name="evyoutube", embedding_function=default_ef)

    results = collection.query(
        query_texts=[query],
        n_results=3
    )
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
            "distance": distance,
            "source": "youtube"
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

    model = SubmindModelFactory.get_model('Ev Chapman Youtube', "content_lookup")
    prompt = ChatPromptTemplate.from_template(SYSTEM_TEMPLATE)
    chain = prompt | model | StrOutputParser()

    context = "\n".join(map(lambda x: x['text'], prepped_results))
    print("Context: ", context)
    response = chain.invoke({"context": context, "question": query})

    return response, prepped_results

def find_content_for_query(query: str):
    yt_answer, youtube_content = get_youtube_content(query)
    ss_answer, substack_content = get_substack_content(query)
    blog_answer, blog_content = get_blog_content(query)
    answer, content = combine_content(query, yt_answer, youtube_content, ss_answer, substack_content, blog_answer, blog_content)
    return answer, content


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
            "distance": distance,
            "source": "youtube"
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

def get_substack_content(query):
    chroma_client = chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)

    embedding_function = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                          model_name="text-embedding-3-small")

    default_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=config('OPENAI_API_KEY'),
                                                             model_name="text-embedding-3-small")
    collection = chroma_client.get_collection(name="engineering_generosity", embedding_function=default_ef)

    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    print(f"Number of results: {len(results['ids'])}")
    prepped_results = []
    existing_ids = set()

    for index, result in enumerate(results['ids'][0]):
        if results['metadatas'][0][index]['title'] in existing_ids:
            continue
        existing_ids.add(results['metadatas'][0][index]['title'])
        metadata = results['metadatas'][0][index]
        print(f"Title: {metadata['title']}")
        text = results['documents'][0][index]
        print(f"Text: {text}")
        distance = results['distances'][0][index]
        print(f"Distance: {distance}")
        prepped_results.append({
            "metadata": metadata,
            "text": text,
            "distance": distance,
            "source": "substack"
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
    print(prepped_results)

    return response, prepped_results

def get_blog_content(query):
    chroma_client = chromadb.HttpClient(host=config('LEOAI_CHROMA_HOST'), port=8000)

    embedding_function = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                          model_name="text-embedding-3-small")

    default_ef = embedding_functions.OpenAIEmbeddingFunction(api_key=config('OPENAI_API_KEY'),
                                                             model_name="text-embedding-3-small")
    collection = chroma_client.get_collection(name="ideasupplychain_blog", embedding_function=default_ef)

    results = collection.query(
        query_texts=[query],
        n_results=10
    )
    print(f"Number of results: {len(results['ids'])}")
    prepped_results = []
    existing_ids = set()

    for index, result in enumerate(results['ids'][0]):
        if results['metadatas'][0][index]['title'] in existing_ids:
            continue
        existing_ids.add(results['metadatas'][0][index]['title'])
        metadata = results['metadatas'][0][index]
        print(f"Title: {metadata['title']}")
        text = results['documents'][0][index]
        print(f"Text: {text}")
        distance = results['distances'][0][index]
        print(f"Distance: {distance}")
        prepped_results.append({
            "metadata": metadata,
            "text": text,
            "distance": distance,
            "source": "blog"
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
    print(prepped_results)
    return response, prepped_results

def combine_content(query, yt_answer, youtube_content, ss_answer, substack_content, blog_answer, blog_content):
    # Combine content
    combined_content = []
    for c in youtube_content:
        combined_content.append(c)
    for c in substack_content:
        combined_content.append(c)
    for c in blog_content:
        combined_content.append(c)



    combined_content.sort(key=lambda x: x['distance'])
    print(list(map(lambda x: x['distance'], combined_content)))
    combined_content = combined_content[:3]

    combined_content_text = []
    for content in combined_content:
        combined_content_text.append(content['text'])

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

    context = "\n".join(combined_content_text)
    print("Context: ", context)
    response = chain.invoke({"context": context, "question": query})

    return response, combined_content