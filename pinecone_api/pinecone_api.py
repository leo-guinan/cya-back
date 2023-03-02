import pinecone
from decouple import config
class PineconeAPI:
    index_name = 'content'
    def __init__(self):
        api_key = config('PINECONE_API_KEY')
        self.pinecone = pinecone.init(api_key=api_key, environment='us-west1-gcp')
        self.index = pinecone.Index(index_name=self.index_name)


    def upsert(self, vectors, namespace=None):
        self.index.upsert(vectors=vectors, namespace=namespace)

    def search(self, query_vector, k=10, metadata=None):
        if not metadata:
            return self.index.query(query_vector,
                        top_k=k)
        else:
            return self.index.query(query_vector,
                                    top_k=k,
                                    filter=metadata)



