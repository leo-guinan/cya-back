import json

from chromadb.config import Settings
from decouple import config
from langchain.vectorstores import Chroma
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from content.snippets import create_snippet
from embeddings.documents import save_document
from embeddings.vectorstore import Vectorstore
from search.models import Link
from spark.manage import add_rss_feed


# Create your views here.
@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes([HasAPIKey])
def search(request):
    body = json.loads(request.body)
    query = body['query']

    vectorstore = Vectorstore()


    results = vectorstore.similarity_search(query, "spark", k=10)
    search_results = []
    for result in results:
        section_id = result.metadata['section']
        # fulltext_id = result['metadata']['fulltext']
        link_id = result.metadata['link']
        link = Link.objects.filter(id=link_id).first()
        snippet = create_snippet(section_id)
        search_results.append({
            "title": link.title,
            "link": link.url,
            "snippet": snippet
        })
    print(search_results)


    return Response({'response': search_results})

