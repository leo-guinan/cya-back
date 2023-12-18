import os
import re
from typing import Callable, Union

from decouple import config
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.prompts import StringPromptTemplate
from langchain.schema import AgentAction, AgentFinish, Document
from langchain.tools import Tool
from langchain.vectorstores import pinecone, Pinecone, Chroma

from cofounder.tools.source import SourceTool




# docs = [
#     Document(page_content=t.description, metadata={"index": i})
#     for i, t in enumerate(ALL_TOOLS)
# ]

embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
# db = Chroma("test", embeddings)
# vector_store = Chroma.from_documents(docs, embeddings)
                # (index, embeddings.embed_query, "text", namespace="user_info"))
# vector_store = FAISS.from_documents(docs, OpenAIEmbeddings())


# retriever = vector_store.as_retriever()





