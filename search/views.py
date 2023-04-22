import json

from decouple import config
from langchain.utilities import BingSearchAPIWrapper
from rest_framework.decorators import permission_classes, api_view, renderer_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from content.snippets import create_snippet
from embeddings.vectorstore import Vectorstore
from search.add import add_searchable_link
from search.models import Link, SearchEngine, SearchableLink


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    query = body['query']
    search_engine = body['search_engine']
    use_base = body['use_base']
    vectorstore = Vectorstore()

    private_results = vectorstore.similarity_search(query, search_engine, k=10)
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
        section_id = result.metadata['section']
        # fulltext_id = result['metadata']['fulltext']
        link_id = result.metadata['link']
        link = Link.objects.filter(id=link_id).first()
        if link is None:
            continue
        snippet = create_snippet(section_id)
        results.append({
            "title": link.title,
            "link": link.url,
            "snippet": snippet
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
