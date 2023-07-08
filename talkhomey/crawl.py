import logging
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup

from crawler.models import CrawlerError
from talkhomey.models import Resource
from talkhomey.vectorstore import Vectorstore

logger = logging.getLogger(__name__)


def process_page(soup: BeautifulSoup, url, parent_resource):
    # Placeholder function
    # Add your scraping code here
    title = soup.title.string if soup.title else url
    description = soup.find("meta", property="og:description")['content'] if soup.find("meta",
                                                                                       property="og:description") else ""
    keywords = soup.find("meta", property="keywords")['content'] if soup.find("meta", property="keywords") else ""

    content = soup.get_text(strip=True)
    print(f"----- Processing page: {soup.title.string} -----")
    child = Resource.objects.create(url=url, title=title, description=description, keywords=keywords, content=content)
    parent_resource.children.add(child)
    parent_resource.save()

    vectorstore = Vectorstore()
    vectorstore.save_resource(child)
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


def crawl(resource):
    url = resource.url

    crawled_urls = set()
    to_crawl = {url}

    while to_crawl:
        url = to_crawl.pop()
        try:
            print(f"----- Crawling: {url} -----")
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            process_page(soup, url, resource)

            crawled_urls.add(url)

            for link in get_all_links(url, url):
                if link not in crawled_urls:
                    to_crawl.add(link)
        except Exception as e:
            CrawlerError.objects.create(url=url, message=str(e))
            logger.error(f"Error crawling {url}: {e}")
