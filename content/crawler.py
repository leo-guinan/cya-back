import logging
from urllib.parse import urljoin, urlparse
import re
import requests
from bs4 import BeautifulSoup
from decouple import config
from langchain.document_loaders import BSHTMLLoader
from langchain.embeddings import OpenAIEmbeddings


class Crawler:
    logger = logging.getLogger(__name__)

    def __init__(self, scraper):
        self.scraper = scraper

    def crawl(self, base_url):
        print(f"----- Crawling: {base_url} -----")

        crawled_urls = set()
        to_crawl = {base_url}
        while to_crawl:
            url = to_crawl.pop()
            try:
                print(f"----- Crawling: {url} -----")
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    continue

                self._process_page(url)
                crawled_urls.add(url)

                for link in self._get_all_links(url, base_url):
                    if link not in crawled_urls:
                        to_crawl.add(link)
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {e}")

    def _process_page(self, url):
        self.scraper.scrape(url)



    def _is_valid(self, url: str) -> bool:
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme)

    def _get_all_links(self, url, root_url):

        headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
        raw_page = requests.get(url, headers=headers)
        soup = BeautifulSoup(raw_page.content, 'html.parser')

        for link in soup.find_all('a'):
            link_href = link.get('href')
            if link_href:
                absolute_url = urljoin(root_url, link_href)
                if self._is_valid(absolute_url) and absolute_url.startswith(root_url):
                    yield absolute_url

