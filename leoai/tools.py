# Import things that are needed generically
from chromadb.config import Settings
from decouple import config
from langchain import VectorDBQA
from langchain.agents import Tool
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import Chroma


# docs = []
# for loader in loaders:
#     docs.extend(loader.load())
# feed
# docs = []
# metas = []
# for entry_idx, entry in enumerate(feed.entries):
#     loader = WebBaseLoader(entry['link'])
#     documents = text_splitter.split_documents(loader.load())
#     docs.extend(documents)

# print()
# print(loader.load())
# print(entry['summary'])
# hhgttf_db = Qdrant.from_documents(docs, embeddings)


class Tools:
    tools = []
    databases = {}
    chains = {}

    def __init__(self):
        embeddings = OpenAIEmbeddings(openai_api_key=config('OPENAI_API_KEY'))
        llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))

        settings = Settings(chroma_api_impl="rest",
                            chroma_server_host="34.205.81.226",
                            chroma_server_http_port=8000)

        hhgttf_db = Chroma(
            collection_name="hhgttf",
            embedding_function=embeddings,
            client_settings=settings)
        self.databases["hhgttf"] = hhgttf_db
        hhgttf = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=hhgttf_db)
        self.chains["hhgttf"] = hhgttf
        self.tools = [
            Tool(
                name="Hitchhiker's Guide To The Future",
                func=hhgttf.run,
                description="useful for when you need to answer questions about future. Input should be a fully formed question."
            ),
            # Tool(
            #     name = "Ruff QA System",
            #     func=ruff.run,
            #     description="useful for when you need to answer questions about ruff (a python linter). Input should be a fully formed question."
            # ),
        ]
