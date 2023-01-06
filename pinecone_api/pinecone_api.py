import pinecone
from decouple import config
class PineconeAPI:
    index_name = 'leo-content'
    def __init__(self):
        api_key = config('PINECONE_API_KEY')
        self.pinecone = pinecone.init(api_key=api_key, environment='us-west1-gcp')
        self.index = pinecone.Index(index_name=self.index_name)


    def upsert(self, vectors):
        self.index.upsert(vectors=vectors)

    def search(self, query_vector, k=10):
        return self.index.query(query_vector,
                    top_k=k)


