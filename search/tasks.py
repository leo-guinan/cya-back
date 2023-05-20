from backend.celery import app
from embeddings.vectorstore import Vectorstore
from search.models import SearchEngine, SearchableLink


@app.task(name="refresh_vectorstore")
def refresh_vectorstore(search_engine):
    engine = SearchEngine.objects.filter(slug=search_engine).first()
    vectorstore = Vectorstore()
    vectorstore.create_collection(search_engine)
    links =  SearchableLink.objects.filter(search_engine=engine).all()
    for link in links:
        vectorstore.add_to_collection(search_engine, [f"{link.title}\n{link.description}"], [str(link.uuid)],
                                       [{"link": link.url.id, "searchable_link": link.id}])