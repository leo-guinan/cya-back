import chromadb
from chromadb.config import Settings
from decouple import config
from langchain.vectorstores import Chroma


class Vectorstore:
    collections = {}

    def __init__(self):
        self.settings = Settings(chroma_api_impl="rest",
                                 chroma_server_host=config('CHROMA_SERVER_HOST'),
                                 chroma_server_http_port=8000)
        client = chromadb.Client(settings=self.settings)
        collections = client.list_collections()
        for collection in collections:
            if collection.name not in self.collections:
                self.collections[collection.name] = Chroma(
                    collection_name=collection.name,
                    client_settings=self.settings)

    def create_collection(self, name):
        collection = Chroma(
            collection_name=name,
            client_settings=self.settings)
        self.collections[name] = collection

    def add_to_collection(self, collection, texts, ids, metadatas):
        self.collections[collection].add_texts(texts=texts, ids=ids, metadatas=metadatas)
