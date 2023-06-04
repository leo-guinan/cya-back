from typing import List

from content.snippets import create_snippet
from decisions.models import MetaSearchEngine, SearchableLink
from embeddings.vectorstore import Vectorstore


def pick_search_engines_to_use(slug, query):
    vectorstore = Vectorstore()
    search_engine_search_engine = MetaSearchEngine.objects.get(slug=slug)
    number_of_results = search_engine_search_engine.search_engines.count()
    search_engines_to_search = vectorstore.similarity_search(query, slug,
                                                             k=number_of_results if number_of_results < 3 else 3)
    return search_engines_to_search


def compile_search_results(search_engines_to_search: List, query):
    results = []
    vectorstore = Vectorstore()

    for search_engine in search_engines_to_search:

        number_of_search_results = search_engine.searchable_links.count()

        intermediate_results = vectorstore.similarity_search(query, search_engine.slug,
                                                        k=number_of_search_results if number_of_search_results < 4 else 4)
        for result in intermediate_results:
            if result.metadata.get('search_engine'):
                continue
            section_id = result.metadata.get('section')
            # fulltext_id = result['metadata']['fulltext']

            link_id = result.metadata['link']
            searchable_link = SearchableLink.objects.filter(id=link_id).first()
            if searchable_link is None:
                continue
            if section_id:
                snippet = create_snippet(section_id)
            else:
                snippet = None
            if searchable_link and searchable_link.title:
                title = searchable_link.title
            else:
                title = "Missing Title"

            if searchable_link and searchable_link.description:
                description = searchable_link.description
            else:
                description = None
            results.append({
                "title": title,
                "link": searchable_link.url.url,
                "snippet": snippet,
                "description": description
            })
    return results
