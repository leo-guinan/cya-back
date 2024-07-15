import re
import uuid
from datetime import datetime
from urllib.parse import urlparse, urljoin
from urllib.request import Request, urlopen

import requests
from bs4 import BeautifulSoup
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pymongo import MongoClient

from prelo.submind.prompts import LEARN_FROM_TEXT_PROMPT
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind


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


def process_page(soup: BeautifulSoup, url, submind: Submind = None, what_to_learn=None):
    title = soup.title.string if soup.title else url
    print(f"----- Processing page: {title} -----")

    content = soup.get_text(strip=True)

    if submind:
        learn_from_page(content, submind, what_to_learn)


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


def crawl(base_url: str, submind: Submind = None, what_to_learn=None):
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
            process_page(soup, url, submind, what_to_learn)

            crawled_urls.add(url)
            if len(crawled_urls) > 50:
                return

            for link in get_all_links(url, base_url):
                if link not in crawled_urls:
                    to_crawl.add(link)
        except Exception as e:
            print(f"Error crawling {url}: {e}")


def scrape(url, submind: Submind = None, what_to_learn=None):
    print(f"----- Crawling: {url} -----")
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
    session = requests.Session()
    session.verify = False
    response = session.get(url, headers=headers)

    if response.status_code != 200:
        return

    soup = BeautifulSoup(response.content, 'html.parser')
    process_page(soup, url, submind, what_to_learn)


def learn_from_page(content: str, submind: Submind, what_to_learn: str):
    current_knowledge = remember(submind)
    model = SubmindModelFactory.get_claude(submind.uuid, "Submind Webpage Learning")
    # model = SubmindModelFactory.get_ollama(submind.uuid, "Submind Webpage Learning")
    print("Current submind knowledge")
    print(current_knowledge)
    learning_prompt = ChatPromptTemplate.from_template(LEARN_FROM_TEXT_PROMPT)
    learning_chain = learning_prompt | model | StrOutputParser()
    learning = learning_chain.invoke({
        "knowledge_base": current_knowledge,
        "what_to_learn": what_to_learn,
        "text": content
    })
    print("New information learned")
    print(learning)

    historical_uuid = str(uuid.uuid4())
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.submind
    previous_doc = db.documents.find_one({"uuid": submind.mindUUID})
    db.document_history.insert_one({
        "uuid": historical_uuid,
        "content": previous_doc["content"],
        "createdAt": previous_doc["createdAt"],
        "documentUUID": previous_doc["uuid"]
    })
    db.documents.update_one({"uuid": submind.mindUUID}, {
        "$set": {"content": f"{previous_doc['content']}\n\n{learning}", "previousVersion": historical_uuid,
                 "updatedAt": datetime.now()}},
                            upsert=True)
