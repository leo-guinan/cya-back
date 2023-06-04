import uuid
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from langchain.text_splitter import TokenTextSplitter

from chat.models import ClientApp, Source
from decisions.models import SearchEngine, MetaSearchEngine, Fulltext, Section, Link
from embeddings.vectorstore import Vectorstore


def process_page(soup: BeautifulSoup, url, parent_link, search_engine_slug, metasearch_engine_slug):
    # Placeholder function
    # Add your scraping code here
    title = soup.title.string if soup.title else url
    child = Link.objects.create(url=url, title=title)
    parent_link.children.add(child)
    parent_link.save()
    content = soup.get_text(strip=True)
    print(f"----- Processing page: {soup.title.string} -----")
    print(content)
    save_content(child, content, search_engine_slug, metasearch_engine_slug)


def is_valid(url: str) -> bool:
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)


def get_all_links(url: str, root_url: str):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
    source_code = requests.get(url, headers=headers)
    soup = BeautifulSoup(source_code.content, 'html.parser')

    for link in soup.find_all('a'):
        link_href = link.get('href')
        if link_href:
            absolute_url = urljoin(root_url, link_href)
            if is_valid(absolute_url) and absolute_url.startswith(root_url):
                yield absolute_url

def crawl(base_url: str, client_app: ClientApp):
    print(f"----- Crawling: {base_url} -----")
    child_meta_search_engine = MetaSearchEngine.objects.create(name="Child Meta Search Engine", slug=str(uuid.uuid4()),
                                                               uuid=str(uuid.uuid4()))
    source = Source.objects.create(url=base_url, title=base_url, metasearch_engine=child_meta_search_engine, app=client_app)

    search_engine = SearchEngine.objects.create(slug=str(uuid.uuid4()),
                                                uuid=str(uuid.uuid4()), url=base_url)
    if not client_app.metasearch_engine:
        client_app.metasearch_engine = MetaSearchEngine.objects.create(name="Meta Search Engine", slug=str(uuid.uuid4()),
                                                                       uuid=str(uuid.uuid4()))
        client_app.metasearch_engine.save()
    child_meta_search_engine.search_engines.add(search_engine)
    child_meta_search_engine.save()

    client_app.metasearch_engine.children.add(child_meta_search_engine)
    client_app.metasearch_engine.save()

    client_app.sources.add(source)
    client_app.save()

    crawled_urls = set()
    to_crawl = {base_url}

    parent_link = Link.objects.create(url=base_url, title=base_url)
    session = requests.Session()
    session.verify = False
    while to_crawl:
        url = to_crawl.pop()
        print(f"----- Crawling: {url} -----")
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
        response = session.get(url, headers=headers)

        if response.status_code != 200:
            continue

        soup = BeautifulSoup(response.content, 'html.parser')
        process_page(soup, url, parent_link, search_engine_slug=search_engine.slug,
                     metasearch_engine_slug=child_meta_search_engine.slug)

        crawled_urls.add(url)

        for link in get_all_links(url, base_url):
            if link not in crawled_urls:
                to_crawl.add(link)


def save_content(link, content, search_engine_slug, metasearch_engine_slug):
    fulltext = Fulltext()
    fulltext.url = link
    fulltext.text = content
    fulltext.save()
    vectorstore = Vectorstore()
    text_splitter = TokenTextSplitter(chunk_size=250, chunk_overlap=10)
    chunks = text_splitter.split_text(content)
    texts = []
    ids = []
    metadatas = []
    for chunk in chunks:
        embedding_id = str(uuid.uuid4())
        section = Section()
        section.fulltext = fulltext
        section.text = chunk
        section.embedding_id = embedding_id
        section.save()
        metadata = {
            'url': link.url,
            'search_engine': search_engine_slug,
            'metasearch_engine': metasearch_engine_slug,
            'fulltext_id': fulltext.id,
            'section_id': section.id,
        }
        texts.append(chunk)
        ids.append(embedding_id)
        metadatas.append(metadata)
    print(search_engine_slug)
    print(metasearch_engine_slug)
    vectorstore.add_to_collection(search_engine_slug, texts, ids, metadatas)
