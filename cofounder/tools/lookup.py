import logging

import pinecone
from decouple import config
from langchain import OpenAI
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone

from coach.tools.tool_class import ToolBase


class LookupTool(ToolBase):

    logger = logging.getLogger(__name__)

    def __init__(self):
        pinecone.init(
            api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=config("PINECONE_ENV"),  # next to api key in console
        )
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"), openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        # db = Chroma("test", embeddings)
        index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
        vectorstore = Pinecone(index,
                               embeddings.embed_query,
                               "text",
                               namespace="information_sources")
        self.retriever = vectorstore.as_retriever()
        llm = OpenAI(openai_api_key=config('OPENAI_API_KEY'), openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })

        self.qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="map_reduce",
            retriever=self.retriever,
            return_source_documents=True,
            verbose=True
        )

    def lookup(self, message):
        return self.qa({"query": message})
        # return self.retriever.get_relevant_documents(message)

    def get_tool(self):
        pass