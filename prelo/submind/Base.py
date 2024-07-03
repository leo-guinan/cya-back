from datetime import datetime

import uuid

import requests
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pymongo import MongoClient

from prelo.submind.prompts import INTEGRATE_LEARNING_PROMPT, LEARN_FROM_TEXT_PROMPT, COMPRESS_KNOWLEDGE_PROMPT
from prelo.submind.tools.web_scraper import crawl, scrape
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember
from submind.models import Submind
from toolkit.tasks import transcribe_youtube_video


class BaseSubmind:
    _submind = None
    def __init__(self, submind_id):
        self._submind = Submind.objects.get(id=submind_id)
        # self.model = SubmindModelFactory.get_claude(self._submind.uuid, "Submind Learning")
        self.model = SubmindModelFactory.get_model(self._submind.uuid, "Submind Webpage Learning")

        self.mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.submind

    def learn_from_youtube_video(self, url, what_to_learn):
        transcript = transcribe_youtube_video(url)
        self.learn_from_text(transcript, what_to_learn)

    def learn_from_webpage(self, url, what_to_learn):
        scrape(url, self._submind, what_to_learn)

    def scan_website(self, url, what_to_learn):
        crawl(url, self._submind, what_to_learn)

    def learn_style(self, text):
        pass

    def generate_text(self, text):
        pass

    def research_topic(self, topic):
        pass

    def google_search(self, query, api_key, cse_id, num_results=5):
        url = f"https://www.googleapis.com/customsearch/v1"
        params = {
            'key': api_key,
            'cx': cse_id,
            'q': query,
            'num': num_results,
        }
        response = requests.get(url, params=params)
        return response.json()

    def learn_from_text(self, text, what_to_learn):
        current_knowledge = remember(self._submind)
        print("Current submind knowledge")
        print(current_knowledge)
        learning_prompt = ChatPromptTemplate.from_template(LEARN_FROM_TEXT_PROMPT)
        learning_chain = learning_prompt | self.model | StrOutputParser()
        learning = learning_chain.invoke({
            "knowledge_base": current_knowledge,
            "what_to_learn": what_to_learn,
            "text": text
        })
        print("New information learned")
        print(learning)

        historical_uuid = str(uuid.uuid4())

        previous_doc = self.db.documents.find_one({"uuid": self._submind.mindUUID})
        self.db.document_history.insert_one({
            "uuid": historical_uuid,
            "content": previous_doc["content"],
            "createdAt": previous_doc["createdAt"],
            "documentUUID": previous_doc["uuid"]
        })
        self.db.documents.update_one({"uuid": self._submind.mindUUID}, {
            "$set": {"content": f"{previous_doc['content']}\n{learning}", "previousVersion": historical_uuid, "updatedAt": datetime.now()}},
                                upsert=True)

    def compress_knowledge(self):
        current_knowledge = remember(self._submind)
        print("Current submind knowledge")
        print(current_knowledge)
        compression_prompt = ChatPromptTemplate.from_template(COMPRESS_KNOWLEDGE_PROMPT)
        compression_chain = compression_prompt | self.model | StrOutputParser()
        compressed_knowledge = compression_chain.invoke({
            "knowledge_base": current_knowledge,
            "topic": self._submind.description
        })
        print("Compressed knowledge")
        print(compressed_knowledge)

        historical_uuid = str(uuid.uuid4())

        previous_doc = self.db.documents.find_one({"uuid": self._submind.mindUUID})
        self.db.document_history.insert_one({
            "uuid": historical_uuid,
            "content": previous_doc["content"],
            "createdAt": previous_doc["createdAt"],
            "documentUUID": previous_doc["uuid"]
        })
        self.db.documents.update_one({"uuid": self._submind.mindUUID}, {
            "$set": {"content": compressed_knowledge, "previousVersion": historical_uuid,
                     "updatedAt": datetime.now()}},
                                     upsert=True)

    @classmethod
    def create_submind(cls, topic, description):
        submind_uuid = str(uuid.uuid4())
        submind_mind_uuid = str(uuid.uuid4())
        submind = Submind.objects.create(uuid=submind_uuid, name=topic, description=description, mindUUID=submind_mind_uuid)
        return cls(submind.id)



