import logging
from typing import List

from decouple import config
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import BaseMessage, HumanMessage, BaseChatMessageHistory

from decisions.models import MetaSearchEngine
from embeddings.vectorstore import Vectorstore

logger = logging.getLogger(__name__)



class PassedInChatHistory(BaseChatMessageHistory):
    _messages = []

    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages

    def add_user_message(self, message) -> None:
        if type(message) == dict:
            message = message['message']
        self._messages.append(HumanMessage(content=message))

    def add_ai_message(self, message) -> None:
        if type(message) == dict:
            message = message['message']
        self._messages.append(HumanMessage(content=message))

    def clear(self) -> None:
        self._messages = []
def respond_to_message(history, message, slug):
    vectorstore = Vectorstore()
    # slug is for metasearch engine. First, have to find the best search engine to search.
    metasearch_engine = MetaSearchEngine.objects.get(slug=slug)
    print(slug)
    search_slug = metasearch_engine.search_engines.first().slug
    print(search_slug)
    chat_history = PassedInChatHistory()
    for item in history:
        if item['speaker'] == 'human':
            chat_history.add_user_message(item)
        else:
            chat_history.add_ai_message(item)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=chat_history)

    llm = ChatOpenAI(openai_api_key=config('OPENAI_API_KEY'), temperature=0)
    # chain = load_qa_with_sources_chain(llm, chain_type="stuff",
    #                                    retriever=vectorstore.get_collection(search_engine).as_retriever())
    chain = ConversationalRetrievalChain.from_llm(llm, vectorstore.get_collection(search_slug).as_retriever(),
                                                  memory=memory)
    response = chain.run(question=message)
    comparison = vectorstore.similarity_search(message, search_slug, 1)
    logger.info(comparison)
    logger.info(response)
    return response