import logging
import os
import uuid

import pinecone
import requests
from decouple import config
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from pymongo import MongoClient

from coach.models import Source, SourceLink
from content.rss import parse_feed, get_link_for_entry
from content.transcriber import Transcriber


class AddContent:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.transcriber = Transcriber()
        self.mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.coach_sources
        pinecone.init(
            api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=config("PINECONE_ENV"),  # next to api key in console
        )
        self.embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'),
                                      headers={
                                          "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
                                      })
        # db = Chroma("test", embeddings)
        self.index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
        self.vectorstore = Pinecone(self.index, self.embeddings.embed_query, "text")


    def add_podcast(self, rss_url, name, description):
        source = Source()
        source.name = name
        source.rss_feed = rss_url
        source.description = description
        source.save()
        feed = parse_feed(rss_url)
        for entry in feed.entries:
            try:
                title, url = get_link_for_entry(entry)
                if url:
                    link = SourceLink()
                    link.source = source
                    link.url = url
                    link.title = title
                    link.save()
                    # download the file and transcribe
                    self.logger.info(f"Downloading {url}")
                    audio_file = self.download_file(url)
                    self.logger.info("Transcribing")
                    transcript_chunks = self.transcribe(audio_file)
                    fulltext = "\n".join(transcript_chunks)
                    fulltext_id = str(uuid.uuid4())
                    self.save_to_mongo(fulltext, fulltext_id)
                    link.fulltext_id = fulltext_id
                    link.save()
                    texts, metadatas, ids = self.build_documents(transcript_chunks, url, link, source)
                    self.logger.info("Adding to pinecone")
                        # now need to save embeddings for each chunk to pinecone
                    self.save_to_pinecone(texts, metadatas, ids)
            except Exception as e:
                self.logger.error(e)
            finally:
                self.delete_file("audio.mp3")

    def download_file(self, url):
        r = requests.get(url)
        with open("audio.mp3", "wb") as f:
            f.write(r.content)
        return "audio.mp3"

    def build_documents(self, transcript_chunks, url, fulltext_id, source):
        texts = []
        metadatas = []
        ids = []
        for chunk in transcript_chunks:
            texts.append(chunk)
            metadatas.append({
                "url": url,
                "content_id": fulltext_id,
                "source_id": source.id,
                "source_name": source.name,
                "source_type": "podcast"
            })
            ids.append(str(uuid.uuid4()))
        return texts, metadatas, ids

    def transcribe(self, audio_file):
        return self.transcriber.transcribe(audio_file)

    def save_to_mongo(self, fulltext, fulltext_id):
        self.db.fulltext.insert_one({"text": fulltext, "fulltext_id": fulltext_id})

    def save_to_pinecone(self, texts, metadatas, ids):
        self.vectorstore.add_texts(texts, metadatas=metadatas, ids=ids, namespace="information_sources")

    def delete_file(self, file_name):
        os.remove(file_name)





    def add_video(self, youtube_url, name):
        pass

    def add_blog(self, blog_url, name):
        pass

    def add_youtube_channel(self, youtube_channel_url, name):
        pass
