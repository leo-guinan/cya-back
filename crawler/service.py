import json
import logging
import re
import uuid
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chains import ConversationalRetrievalChain, llm
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders import BSHTMLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import TokenTextSplitter

from chat.models import ClientApp, Source
from crawler.models import CrawlerError
from decisions.models import SearchEngine, MetaSearchEngine, Fulltext, Section, Link
from embeddings.vectorstore import Vectorstore
logger = logging.getLogger(__name__)


def url_to_filename(url):
    safe_name = re.sub(r"[^\w\-_]", "_", url)
    return safe_name

def clean_string(input_string):
    cleaned_string = "".join(char for char in input_string.lower() if char.isalpha())
    return cleaned_string

def download_file(download_url, file_name):
    req = Request(download_url, headers={'User-Agent' : "Magic Browser"})

    response = urlopen(req)
    f = open(file_name, 'wb')
    f.write(response.read())
    f.close()
def process_page(soup: BeautifulSoup, url, parent_link, search_engine_slug_match, search_engine_slug_not_match, metasearch_engine_slug):
    # Placeholder function
    # Add your scraping code here
    title = soup.title.string if soup.title else url
    child = Link.objects.create(url=url, title=title)
    parent_link.children.add(child)
    parent_link.save()
    content = soup.get_text(strip=True)
    print(f"----- Processing page: {soup.title.string} -----")
    print(content)
    file_name = url_to_filename(url)
    download_file(url, file_name)
    loader = BSHTMLLoader(file_name)

    data = loader.load()
    collection = "TalkHomey-testing_site"
    embeddings = OpenAIEmbeddings(openai_api_key=config('OPENAI_API_KEY'))
    # settings = Settings(chroma_api_impl="rest",
    #                     chroma_server_host=config('CHROMA_SERVER_HOST'),
    #                     chroma_server_http_port=8000)
    # chroma_collection = Chroma(
    #             embedding_function=embeddings,
    #             collection_name=collection,
    #             client_settings=settings)
    # text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    # docs = text_splitter.split_documents(data)


    llm = ChatOpenAI(openai_api_key=config('OPENAI_API_KEY'), temperature=0, model="gpt-4")

    template = """
        Based on this webpage, it this a listing for a single specific property?
        URL: {url}


        Respond "yes" or "no"
        No prose
        """

    prompt = PromptTemplate(
        input_variables=["url"],
        template=template,
    )
    content = soup.get_text(strip=True)

    chain = LLMChain(llm=llm, prompt=prompt)
    answer = chain.run(
        # page_content=content,
        url=url
    )
    print(clean_string(answer))
    if clean_string(answer) == "yes":
        save_property_info(child, content, search_engine_slug_match, metasearch_engine_slug)

    else:
        save_content(child, content, search_engine_slug_not_match, metasearch_engine_slug)
        # chain = load_qa_with_sources_chain(llm, chain_type="stuff",
        # retriever=vectorstore.get_collection(search_engine).as_retriever())


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
    categories = client_app.search_engine_categories.all()
    # for now, just create the pieces needed for talkhomey. Can make it work for other versions later

    child_meta_search_engine = MetaSearchEngine.objects.create(name="Child Meta Search Engine", slug=str(uuid.uuid4()),
                                                               uuid=str(uuid.uuid4()))
    source = Source.objects.create(url=base_url, title=base_url, metasearch_engine=child_meta_search_engine, app=client_app)
    search_engine_uuid = str(uuid.uuid4())
    search_engine_match = SearchEngine.objects.create(slug=f'{search_engine_uuid}-match', title=f'{search_engine_uuid}-match',
                                                uuid=str(uuid.uuid4()), url=base_url)
    search_engine_non_match = SearchEngine.objects.create(slug=f'{search_engine_uuid}-non-match',
                                                      title=f'{search_engine_uuid}-non-match',
                                                      uuid=str(uuid.uuid4()), url=base_url)
    if not client_app.metasearch_engine:
        client_app.metasearch_engine = MetaSearchEngine.objects.create(name="Meta Search Engine", slug=str(uuid.uuid4()),
                                                                       uuid=str(uuid.uuid4()))
        client_app.metasearch_engine.save()
    child_meta_search_engine.search_engines.add(search_engine_match)
    child_meta_search_engine.search_engines.add(search_engine_non_match)
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
        try:
            print(f"----- Crawling: {url} -----")
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
            response = session.get(url, headers=headers)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            process_page(soup, url, parent_link, search_engine_slug_match=f'{search_engine_uuid}-match',
                         search_engine_slug_not_match=f'{search_engine_uuid}-non-match',
                         metasearch_engine_slug=child_meta_search_engine.slug)

            crawled_urls.add(url)

            for link in get_all_links(url, base_url):
                if link not in crawled_urls:
                    to_crawl.add(link)
        except Exception as e:
            CrawlerError.objects.create(url=url, message=str(e))
            logger.error(f"Error crawling {url}: {e}")

def save_content(link, content, search_engine_slug, metasearch_engine_slug):
    print("Saving content")
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

def save_property_info(link, content, search_engine_slug, metasearch_engine_slug):
    print("Saving property info")
    vectorstore = Vectorstore()
    llm = ChatOpenAI(openai_api_key=config('OPENAI_API_KEY'), temperature=0, model="gpt-4")
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chat_chain = ConversationalRetrievalChain.from_llm(llm, vectorstore.get_collection("").as_retriever(),
                                                       memory=memory)
    property_information = chat_chain.run(
        question="What information should I know about this property? Return the answer in JSON. No prose.")
    print(property_information)
    fulltext = Fulltext()
    fulltext.url = link
    fulltext.text = content
    fulltext.save()
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
        try:
            metadatas.append(metadata.update(json.loads(property_information)))
        except:
            metadatas.append(metadata.update({"raw_property_information": property_information}))
    print(search_engine_slug)
    print(metasearch_engine_slug)
    vectorstore.add_to_collection(search_engine_slug, texts, ids, metadatas)

