import json
import logging
from typing import List

from decouple import config
from langchain import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.schema import HumanMessage, AIMessage, BaseChatMessageHistory, BaseMessage
from langchain.utilities import BingSearchAPIWrapper
from rest_framework.decorators import permission_classes, api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from content.snippets import create_snippet
from embeddings.vectorstore import Vectorstore
from search.add import add_searchable_link
from search.models import Link, SearchEngine, SearchableLink, Query

logger = logging.getLogger(__name__)

# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    query = body['query']
    search_engine = body['search_engine']
    use_base = body['use_base']
    engine = SearchEngine.objects.filter(slug=search_engine).first()
    if not engine:
        return Response({'response': 'Search engine not found'}, status=404)
    saved_query = Query()
    saved_query.query = query
    saved_query.search_engine = engine
    saved_query.save()
    vectorstore = Vectorstore()
    number_of_results = SearchableLink.objects.filter(search_engine__slug=search_engine).count()
    private_results = vectorstore.similarity_search(query, search_engine,
                                                    k=number_of_results if number_of_results < 10 else 10)
    results = []

    if use_base:
        search = BingSearchAPIWrapper(bing_subscription_key=config('BING_SUBSCRIPTION_KEY'),
                                      bing_search_url=config('BING_SEARCH_URL'))
        public_results = search.results(query, 5)
        for result in public_results:
            results.append({
                "title": result['title'],
                "link": result['link'],
                "snippet": result['snippet']
            })

    for result in private_results:

        section_id = result.metadata.get('section')
        # fulltext_id = result['metadata']['fulltext']
        link_id = result.metadata['link']
        searchable_link_id = result.metadata['searchable_link']
        link = Link.objects.filter(id=link_id).first()
        searchable_link = SearchableLink.objects.filter(id=searchable_link_id).first()
        if link is None:
            continue
        if section_id:
            snippet = create_snippet(section_id)
        else:
            snippet = None
        results.append({
            "title": searchable_link.title if searchable_link.title else link.title,
            "link": link.url,
            "snippet": snippet,
            "description": searchable_link.description if searchable_link.description else None,
        })

    return Response({'response': results})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def add(request):
    body = json.loads(request.body)
    url = body['url']
    title = body['title']
    description = body['description']
    image = body['image']
    search_engine = body['search_engine']
    add_searchable_link(search_engine, title, url, description, image)
    return Response({'response': 'success'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def create_search_engine(request):
    body = json.loads(request.body)
    search_engine = body['search_engine']
    vectorstore = Vectorstore()
    vectorstore.create_collection(search_engine)
    return Response({'response': 'success'})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def list_links(request):
    body = json.loads(request.body)
    search_engine = body['search_engine']
    engine = SearchEngine.objects.filter(slug=search_engine).first()
    searchable_links = SearchableLink.objects.filter(search_engine=engine).all()
    links = []
    for link in searchable_links:
        links.append({
            'id': link.id,
            'title': link.title,
            'url': link.url.url,
            'description': link.description,
            'image': link.image
        })

    return Response({'response': links})


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def get_queries(request):
    body = json.loads(request.body)
    search_engine = body['search_engine']
    engine = SearchEngine.objects.filter(slug=search_engine).first()
    queries = Query.objects.filter(search_engine=engine).all()
    queries_list = []
    for query in queries:
        queries_list.append({
            'id': query.id,
            'query': query.query,
            'created_at': query.created_at
        })
    return Response({'response': queries_list})


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


@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def chat(request):
    body = json.loads(request.body)
    search_engine = body['search_engine']
    history = body['history']
    message = body['message']
    vectorstore = Vectorstore()
    template = """Assistant is a large language model trained by OpenAI.

    Assistant is designed to be able to assist with a wide range of tasks, from answering simple questions to providing in-depth explanations and discussions on a wide range of topics. As a language model, Assistant is able to generate human-like text based on the input it receives, allowing it to engage in natural-sounding conversations and provide responses that are coherent and relevant to the topic at hand.

    Assistant is constantly learning and improving, and its capabilities are constantly evolving. It is able to process and understand large amounts of text, and can use this knowledge to provide accurate and informative responses to a wide range of questions. Additionally, Assistant is able to generate its own text based on the input it receives, allowing it to engage in discussions and provide explanations and descriptions on a wide range of topics.

    Overall, Assistant is a powerful tool that can help with a wide range of tasks and provide valuable insights and information on a wide range of topics. Whether you need help with a specific question or just want to have a conversation about a particular topic, Assistant is here to assist.

    {history}
    Human: {human_input}
    Assistant:"""

    prompt = PromptTemplate(
        input_variables=["history", "human_input"],
        template=template
    )
    chat_history = PassedInChatHistory()
    print(history)
    for item in history:
        if item['speaker'] == 'human':
            chat_history.add_user_message(item)
        else:
            chat_history.add_ai_message(item)
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, chat_memory=chat_history)

    llm = ChatOpenAI(openai_api_key=config('OPENAI_API_KEY'), temperature=0)
    # chain = load_qa_with_sources_chain(llm, chain_type="stuff",
    #                                    retriever=vectorstore.get_collection(search_engine).as_retriever())
    chain = ConversationalRetrievalChain.from_llm(llm, vectorstore.get_collection(search_engine).as_retriever(),
                                                  memory=memory)
    response = chain.run(question=message)
    comparison = vectorstore.similarity_search(message, search_engine, 1)
    logger.info(comparison)
    logger.info(response)
    return Response({'response': response})
