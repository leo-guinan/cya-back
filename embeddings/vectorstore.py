import chromadb
from chromadb.config import Settings
from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma


class Vectorstore:

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(openai_api_key=config('OPENAI_API_KEY'))
        self.settings = Settings(chroma_api_impl="rest",
                                 chroma_server_host=config('CHROMA_SERVER_HOST'),
                                 chroma_server_http_port=8000)
        client = chromadb.Client(settings=self.settings)

    def create_collection(self, name):
        collection = Chroma(
            embedding_function=self.embeddings,
            collection_name=name,
            client_settings=self.settings)

    def add_to_collection(self, collection, texts, ids, metadatas):
        chroma_collection = Chroma(
            embedding_function=self.embeddings,
            collection_name=collection,
            client_settings=self.settings)
        print(metadatas)
        chroma_collection.add_texts(texts=texts, ids=ids, metadatas=metadatas)

    def similarity_search(self, query, collection, k=10):
        chroma_collection = Chroma(
            embedding_function=self.embeddings,
            collection_name=collection,
            client_settings=self.settings)
        return chroma_collection.similarity_search(query, k=k)

    def get_collection(self, name):
        return Chroma(
            embedding_function=self.embeddings,
            collection_name=name,
            client_settings=self.settings)

