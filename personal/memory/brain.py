import pinecone
from bson import ObjectId
from decouple import config
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.vectorstores import Pinecone
from pymongo import MongoClient

from cofounder.agent.remember_agent import RememberAgent


class Brain:
    def __init__(self, session_id, user_id, purpose=""):
        self.mongo_client = MongoClient(config('PERSONAL_MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.cofounder
        self.session_id = session_id
        self.user_id = user_id
        self.purpose = purpose
        self.base_system_message = f"""
         {self.profile}

                                   You are speaking to your co-founder, {self.founder_name}. {self.founder_profile}



                                   You are a cofounder of {self.business_name}.
                                   Here are the details about about the business:
                                   {self.business_profile}

                                    Here's what you know about the business:
                                    

                                   """
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )
        internal_message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=f"internal_{session_id}"
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=message_history,
                                               input_key="human_input", return_messages=True)
        self.internal_memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=internal_message_history,
                                                        return_messages=True)
        self.llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                              openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        self.quick_llm = ChatOpenAI(temperature=0.7, openai_api_key=config('OPENAI_API_KEY'),
                                    model_name="gpt-3.5-turbo",
                                    openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        pinecone.init(
            api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=config("PINECONE_ENV"),  # next to api key in console
        )
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        # db = Chroma("test", embeddings)
        index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
        self.vectordb_cards = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source_cards")
        self.vectordb_knowledge = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source")
        self.memory_agent = RememberAgent(user_id)