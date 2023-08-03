import logging
import re
from urllib.request import Request, urlopen

import requests
import uuid
from bs4 import BeautifulSoup
from decouple import config
from langchain.document_loaders import BSHTMLLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter


class Scraper:
    logger = logging.getLogger(__name__)
    def __init__(self, client):
        self.client = client


    def scrape(self, url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:15.0) Gecko/20100101 Firefox/15.0.1'}
            raw_page = requests.get(url, headers=headers)
            soup = BeautifulSoup(raw_page.content, 'html.parser')
            print(f"----- Processing page: {soup.title.string} -----")

            file_name = self._url_to_filename(url)
            self._download_file(url, file_name)
            loader = BSHTMLLoader(file_name)

            data = loader.load()
            # split data
            text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
            documents = text_splitter.split_documents(data)
            self.client.add_documents(documents)
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")





    def _url_to_filename(self, url):
        safe_name = re.sub(r"[^\w\-_]", "_", url)
        return safe_name

    def _clean_string(self, input_string):
        cleaned_string = "".join(char for char in input_string.lower() if char.isalpha())
        return cleaned_string

    def _download_file(self, download_url, file_name):
        req = Request(download_url, headers={'User-Agent': "Magic Browser"})

        response = urlopen(req)
        f = open(file_name, 'wb')
        f.write(response.read())
        f.close()
