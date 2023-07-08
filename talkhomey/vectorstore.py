import uuid
from urllib.request import urlopen

import chromadb
from chromadb.config import Settings
from decouple import config
from langchain.document_loaders import BSHTMLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import TokenTextSplitter
from langchain.vectorstores import Chroma
from requests import Request

from talkhomey.models import ResourceChunk


class Vectorstore:

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=config('OPENAI_API_KEY'))
        self.settings = Settings(chroma_api_impl="rest",
                                 chroma_server_host=config('CHROMA_TALKHOMEY_SERVER_HOST'),
                                 chroma_server_http_port=8000)
        client = chromadb.Client(settings=self.settings)

    def create_collection(self, name, title, description, uuid):
        Chroma(
            embedding_function=self.embeddings,
            collection_name=name,
            client_settings=self.settings)

    def add_to_collection(self, texts, ids, metadatas):
        chroma_collection = Chroma(
            embedding_function=self.embeddings,
            collection_name="talkhomey",
            client_settings=self.settings)
        chroma_collection.add_texts(texts=texts, ids=ids, metadatas=metadatas)

    def similarity_search(self, query, k=10):
        chroma_collection = Chroma(
            embedding_function=self.embeddings,
            collection_name="talkhomey",
            client_settings=self.settings)
        return chroma_collection.similarity_search(query, k=k)

    def get_collection(self):
        return Chroma(
            embedding_function=self.embeddings,
            collection_name="talkhomey",
            client_settings=self.settings)

    def save_resource(self, resource):
        print("Saving content")
        text_splitter = TokenTextSplitter(chunk_size=250, chunk_overlap=10)
        chunks = text_splitter.split_text(resource.content)
        texts = []
        ids = []
        metadatas = []
        for chunk in chunks:
            embedding_id = str(uuid.uuid4())
            section = ResourceChunk()

            section.save()
            metadata = {
                'url': resource.url,
                'name': resource.title,
                'description': resource.description,
            }
            texts.append(chunk)
            ids.append(embedding_id)
            metadatas.append(metadata)
        self.add_to_collection(texts, ids, metadatas)
