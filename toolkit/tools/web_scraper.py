import sys
from datetime import datetime

import requests
from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_pinecone  import PineconeVectorStore
from pinecone import Pinecone
import uuid
from langchain_experimental.text_splitter import SemanticChunker
from langchain_text_splitters import RecursiveCharacterTextSplitter
import json
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import re

from pymongo import MongoClient

from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind

LEARNING_FROM_WEBPAGE_PROMPT = """
You are a powerful submind that is learning about someone so that you can figure out how to think exactly like them.
You have been given a webpage to learn from. You need to read the page and learn as much as you can about the person.

Here's what you know about the person so far: {submind}

Here's the webpage you need to learn from: {webpage}

Update what you know with any relevant information you learn from the webpage.

"""

def add_page_to_vectorstore(webpage_text, webpage_name, webpage_url, namespace):
    pc = Pinecone(api_key=config('CRAWLER_PINECONE_API_KEY'))
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=config("OPENAI_API_KEY"),
        openai_api_base=config('OPENAI_API_BASE'),
        headers={
            "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
        })
    index = pc.Index(config('CRAWLER_PINECONE_INDEX_NAME'), host=config('CRAWLER_PINECONE_HOST'))
    vectorstore = PineconeVectorStore(index, embeddings, "text")

    webpages = {}
    text_splitter = SemanticChunker(embeddings)
    backup_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
        is_separator_regex=False,
    )

    chunks = text_splitter.split_text(webpage_text)
    metadatas = []
    ids = []
    chunks_to_save = []
    webpage_id = str(uuid.uuid4())
    webpages[namespace] = {
        f'{webpage_id}': {
            "title": webpage_name,
            "url": webpage_url
        }
    }
    for chunk in chunks:
        chunk_id = str(uuid.uuid4())
        metadata = {
            "webpage_id": webpage_id,
            "chunk_id": chunk_id,
            "webpage_name": webpage_name,
            "url": webpage_url,
            "text": chunk
        }

        # test metadata size
        size = sys.getsizeof(json.dumps(metadata))

        if size > 40960:
            # need to split into smaller chunks
            smaller_chunks = backup_text_splitter.split_text(chunk)
            for smaller_chunk in smaller_chunks:
                smaller_id = str(uuid.uuid4())

                smaller_metadata = {
                    "webpage_id": webpage_id,
                    "chunk_id": smaller_id,
                    "webpage_name": webpage_name,
                    "url": webpage_url,
                    "text": smaller_chunk
                }
                metadatas.append(smaller_metadata)
                ids.append(smaller_id)
                chunks_to_save.append(smaller_chunk)
            continue
        else:
            chunks_to_save.append(chunk)
            metadatas.append(metadata)
            ids.append(chunk_id)

    vectorstore.add_texts(chunks_to_save, metadatas=metadatas, ids=ids, namespace=namespace)

def url_to_filename(url):
    safe_name = re.sub(r"[^\w\-_]", "_", url)
    return safe_name


def clean_string(input_string):
    cleaned_string = "".join(char for char in input_string.lower() if char.isalpha())
    return cleaned_string


def download_file(download_url, file_name):
    req = Request(download_url, headers={'User-Agent': "Magic Browser"})

    response = urlopen(req)
    f = open(file_name, 'wb')
    f.write(response.read())
    f.close()


def process_page(soup: BeautifulSoup, url, namespace, submind: Submind = None):
    # Placeholder function
    # Add your scraping code here
    title = soup.title.string if soup.title else url
    content = soup.get_text(strip=True)
    print(f"----- Processing page: {soup.title.string} -----")
    print(content)
    file_name = url_to_filename(url)
    download_file(url, file_name)

    content = soup.get_text(strip=True)

    if submind:
        learn_from_page(content, submind)

    add_page_to_vectorstore(content, title, url, namespace)


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


def crawl(base_url: str, namespace: str, submind: Submind = None):
    print(f"----- Crawling: {base_url} -----")

    crawled_urls = set()
    to_crawl = {base_url}

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
            process_page(soup, url, namespace, submind)

            crawled_urls.add(url)

            for link in get_all_links(url, base_url):
                if link not in crawled_urls:
                    to_crawl.add(link)
        except Exception as e:
            print(f"Error crawling {url}: {e}")


def scrape(url, session, namespace, submind: Submind=None):

    print(f"----- Crawling: {url} -----")
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    process_page(soup, url, namespace, submind)

def learn_from_page(content: str, submind: Submind):
    submind_document = remember(submind)
    model = SubmindModelFactory.get_model(submind.uuid, "learning_from_webscraping")

    prompt = ChatPromptTemplate.from_template(LEARNING_FROM_WEBPAGE_PROMPT)
    chain = prompt | model | StrOutputParser()

    response = chain.invoke(
        {"submind": submind_document,
         "webpage": content,
         })
    print(response)


    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    historical_uuid = str(uuid.uuid4())

    previous_doc = db.documents.find_one({"uuid": submind.mindUUID})
    db.document_history.insert_one({
        "uuid": historical_uuid,
        "content": previous_doc["content"],
        "createdAt": previous_doc["createdAt"],
        "documentUUID": previous_doc["uuid"]
    })
    db.documents.update_one({"uuid": submind.mindUUID}, {
        "$set": {"content": response, "previousVersion": historical_uuid, "updatedAt": datetime.now()}},
                            upsert=True)

