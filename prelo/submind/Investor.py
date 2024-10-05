from datetime import datetime

import requests
import uuid
from decouple import config
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from prelo.submind.Base import BaseSubmind
from prelo.submind.prompts import ASK_SUBMIND_ABOUT_SELF_PROMPT, COMPRESS_INVESTOR_KNOWLEDGE_PROMPT
from submind.memory.memory import remember
from submind.models import Submind


class InvestorSubmind(BaseSubmind):

    def learn_firm_thesis(self, firm_name, web_page_url):
        self.scan_website(web_page_url, f"learn the investment thesis of {firm_name}")

    def learn_personal_thesis(self):
        pass

    def learn_personal_style(self):
        pass





    def find_links_about_investor(self, person_name: str):
        # Placeholder function
        # Add your scraping code here
        # Replace these with your actual API key and CSE ID
        api_key = config('CUSTOM_SEARCH_API_KEY')
        cse_id = config('CUSTOM_SEARCH_ENGINE_ID')

        # Investor's name

        # Search queries based on the instructions
        queries = [
            f'{person_name} investor',
            f'{person_name} podcast',
            f'{person_name} blog',
            f'{person_name} interview',
            f'{person_name} news',
        ]
        session = requests.Session()
        session.verify = False
        for query in queries:
            print(f"Searching for: {query}")
            results = self.google_search(query, api_key, cse_id)
            if 'items' in results:
                for item in results['items']:
                    print("Crawling...")
                    self.learn_from_webpage(item['link'], f"create a profile of this investor: {person_name}. learn about who they are, what they value personally, and what they value in the companies they invest in.")
                    print(f"Title: {item['title']}")
                    print(f"Link: {item['link']}")
                    print(f"Snippet: {item['snippet']}")
                    print()
            else:
                print("No results found.")
            print("=" * 40)

    def learn_about_person(self, person_name: str):
        self.find_links_about_investor(person_name)
        # podcast_search(person_name, submind)

    def compress_knowledge(self):
        current_knowledge = remember(self._submind)
        print("Current submind knowledge")
        print(current_knowledge)
        compression_prompt = ChatPromptTemplate.from_template(COMPRESS_INVESTOR_KNOWLEDGE_PROMPT)
        compression_chain = compression_prompt | self.model | StrOutputParser()
        compressed_knowledge = compression_chain.invoke({
            "knowledge_base": current_knowledge,
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
        
    def ask(self, question: str):
        current_knowledge = remember(self._submind)
        ask_prompt = ChatPromptTemplate.from_template(ASK_SUBMIND_ABOUT_SELF_PROMPT)
        ask_chain = ask_prompt | self.model | StrOutputParser()
        answer = ask_chain.invoke({
            "knowledge_base": current_knowledge,
            "question": question
        })
        return answer


    @classmethod
    def create_submind_for_investor(cls, investor_name: str, firm_name:str, firm_url:str):
        submind_uuid = str(uuid.uuid4())
        submind_mind_uuid = str(uuid.uuid4())
        submind = Submind.objects.create(uuid=submind_uuid, name=investor_name, description=f"Submind for {investor_name} at {firm_name}", mindUUID=submind_mind_uuid)
        investor_submind = cls(submind.id)
        investor_submind.learn_firm_thesis(firm_name, firm_url)
        investor_submind.learn_about_person(investor_name)
        investor_submind.compress_knowledge()
        return investor_submind


