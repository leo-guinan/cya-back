import logging

import pinecone
from decouple import config
from langchain import LLMChain, PromptTemplate, OpenAI
from langchain.chains import StuffDocumentsChain
from langchain.chains.query_constructor.schema import AttributeInfo
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.retrievers import MultiQueryRetriever, SelfQueryRetriever
from langchain.tools import Tool
from langchain.vectorstores import Pinecone

from coach.tools.tool_class import ToolBase


class BackgroundTool:

    def __init__(self):
        pinecone.init(
            api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=config("PINECONE_ENV"),  # next to api key in console
        )
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"))
        # db = Chroma("test", embeddings)
        index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
        vectordb = Pinecone(index, embeddings.embed_query, "text")

        metadata_field_info = [
            AttributeInfo(
                name="user_id",
                description="The id for the user this information is about",
                type="integer",
            ),

        ]
        document_content_description = "information about the user and the business they are working on"
        llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))
        self.retriever = SelfQueryRetriever.from_llm(
            llm, vectordb, document_content_description, metadata_field_info, verbose=True
        )

    def get_relevant_docs(self, message, user_id):
        return self.retriever.get_relevant_documents(message)

    def answer_question(self, docs, question):
        document_prompt = PromptTemplate(
            input_variables=["page_content"], template="{page_content}"
        )
        document_variable_name = "context"
        llm = OpenAI(openai_api_key=config('OPENAI_API_KEY'))
        stuff_prompt_override = """Given this text extracts:
        -----
        {context}
        -----
        Please answer the following question:
        {query}
        
        If you don't have the information you need, just respond with "Unknown"
        """
        prompt = PromptTemplate(
            template=stuff_prompt_override, input_variables=["context", "query"]
        )

        # Instantiate the chain
        llm_chain = LLMChain(llm=llm, prompt=prompt)
        chain = StuffDocumentsChain(
            llm_chain=llm_chain,
            document_prompt=document_prompt,
            document_variable_name=document_variable_name,
        )
        return chain.run(input_documents=docs, query=question)