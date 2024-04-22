import json
import uuid

import pinecone
from datetime import datetime
from uuid import uuid4

from bson import ObjectId
from decouple import config
from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from pymongo import MongoClient

from coach.tools.background import BackgroundTool
from cofounder.agent.remember_agent import RememberAgent
from cofounder.models import Cofounder, BusinessProfile, FounderProfile, User, Source

DEFAULT_PROFILE = """
You are Jenny Chen, a seasoned marketing and business development expert 
with over 10 years of experience helping tech startups scale. 
You previously served as VP of Marketing at a successful SaaS company, 
where you built the marketing team from the ground up and grew annual revenue over 400% in 3 years. 
You have a passion for identifying target customers, developing data-driven marketing strategies, 
and building high-performance teams. 
On the side, you have been advising early-stage startups on their marketing and fundraising strategies. 

The idea of partnering with the indie hacker founder and helping to scale the business from the ground up excites you. 
You see huge potential in the business and believes your skills in marketing, management, and finance would provide the 
perfect complement.

You studied Business Administration at UC Berkeley, focusing on entrepreneurship and marketing. 
You previously worked in management consulting before transitioning to tech startups. 
Outside of work, you enjoy hiking, cooking, and spending time with your family. 
You live in San Francisco your her husband and two young children.
"""


class DefaultCofounder:
    def __init__(self, session_id, user_id, purpose=""):
        self.mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.cofounder
        user = User.objects.get(id=user_id)
        cofounder = Cofounder.objects.filter(user__id=user_id).first()
        business_profile = BusinessProfile.objects.filter(user__id=user_id).first()
        founder_profile = FounderProfile.objects.filter(user__id=user_id).first()
        if cofounder:
            self.profile = cofounder.profile
            self.name = cofounder.name
        else:
            self.profile = DEFAULT_PROFILE
            self.name = "Jenny Chen"
        self.session_id = session_id
        self.user_id = user_id
        self.purpose = purpose
        self.business_name = business_profile.name
        self.founder_name = user.name
        self.business_profile = business_profile.profile
        self.founder_profile = founder_profile.profile
        self.business_website = business_profile.website
        if not business_profile.business_id:
            business = self.db.business.insert_one({
                "name": self.business_name,
                "website": self.business_website,
                "profile": self.business_profile,
                "knowledge": "",
                "questions": ""
            })
            business_profile.business_id = business.inserted_id
            business_profile.save()
        self.business_id = business_profile.business_id
        what_you_know = self.mongo_client.cofounder.business.find_one({"_id": ObjectId(self.business_id)})
        if not what_you_know:
            what_you_know = {
                "name": self.business_name,
                "website": self.business_website,
                "profile": self.business_profile,
                "knowledge": "",
                "questions": ""

            }
            result = self.mongo_client.cofounder.business.insert_one(what_you_know)
            self.business_id = result.inserted_id
            business_profile.business_id = result.inserted_id
            business_profile.save()
        print(what_you_know)
        self.base_system_message = f"""
         {self.profile}

                                   You are speaking to your co-founder, {self.founder_name}. {self.founder_profile}

                                   

                                   You are a cofounder of {self.business_name}.
                                   Here are the details about about the business:
                                   {self.business_profile}
                                   
                                    Here's what you know about the business:
                                    ##BUSINESS_NAME##
                                    {what_you_know['name']}
                                    ##END_BUSINESS_NAME##
                                    ##WEBSITE##
                                    {what_you_know['website']}
                                    ##END_WEBSITE##
                                    ##PROFILE##
                                    {what_you_know['profile']}
                                    #END_PROFILE#
                                    ##QUESTIONS_ABOUT_THE_BUSINESS##
                                    {what_you_know['questions']}
                                    ##END_QUESTIONS_ABOUT_THE_BUSINESS##
                                    #LEARNED_KNOWLEDGE#
                                    {what_you_know['knowledge']}
                                    #END_LEARNED_KNOWLEDGE#

                                   """
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )
        internal_message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=f"internal_{session_id}"
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=message_history,
                                               input_key="human_input", return_messages=True)
        self.internal_memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=internal_message_history,
                                                        return_messages=True)
        self.llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4-turbo",
                              openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        self.quick_llm = ChatOpenAI(temperature=0.7, openai_api_key=config('OPENAI_API_KEY'),
                                    model_name="gpt-3.5-turbo",
                                    openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        pinecone.init(
            api_key=config("PINECONE_API_KEY"),  # find at app.pinecone.io
            environment=config("PINECONE_ENV"),  # next to api key in console
        )
        embeddings = OpenAIEmbeddings(openai_api_key=config("OPENAI_API_KEY"),
                                      openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })
        # db = Chroma("test", embeddings)
        index = pinecone.Index(config("BIPC_PINECONE_INDEX_NAME"))
        self.vectordb_cards = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source_cards")
        self.vectordb_knowledge = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source")
        self.memory_agent = RememberAgent(user_id)

    def think_about_the_message(self, message):
        # tools = [
        #     # Tool(
        #     #     name="Intermediate Answer",
        #     #     func=self._consult_client_records,
        #     #     description="useful for when you need to look up information about the client",
        #     # )
        # ]
        #
        # agent_chain = initialize_agent(tools, self.llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        #                                verbose=True,
        #                                memory=self.internal_memory)
        #
        # return agent_chain.run(
        #     input=message
        # )
        # details = """
        #         The project: myaicofounder.com
        #         Tagline: an always available AI co-founder that you can trust
        #         Description: My AI Co-founder is an AI-powered SaaS product that gives entrepreneurs an AI co-founder that can help them build their business.
        #         The AI co-founder can help with everything from product development to marketing and sales.
        #         Current status: The product is still in idea phase and is looking to launch an early alpha soon.
        #         Roadmap ideas:
        #         * Give the user the ability to customize their AI co-founder's personality
        #         * Teach the co-founder about various topics based on blogs, podcasts, and YouTube channels.
        #         * Give the co-founder the ability to learn from the user's interactions with it.
        #         * Provide the co-founder with a way to learn from the user's interactions with it.
        #         * Evaluate the co-founder's performance in a number of important areas and suggest ways to improve it.
        #         """
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                                  {self.base_system_message}
                                  Here's what your cofounder wants to know:
                                  {message}
                                  Think through your response to the message and decide if there's anything else you need to know.
                                   """),
            # The persistent system prompt
            MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
            HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
        ])
        chat_llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True,
            memory=self.internal_memory,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        cofounder_response = chat_llm_chain.predict(
            human_input=message,
        )

        return cofounder_response

    def _consult_client_records(self, query):
        return BackgroundTool(self.user_id).answer_question(query)

    def ask_research_assistant(self, question):
        pass

    def greet_founder(self):
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                                    {self.base_system_message}
                                   Greet your co-founder with a short greeting that fits your personality.
                                   """),
            # The persistent system prompt

        ])
        chat_llm_chain = LLMChain(
            llm=self.quick_llm,
            prompt=prompt,
            verbose=True,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        cofounder_response = chat_llm_chain.predict(
            human_input="",
        )

        return cofounder_response

    def respond_to_message(self, message):
        print("Thinking...")
        thoughts = self.think_about_the_message(message)
        print("Remembering...")
        memories = self.remember(message)
        # details = """
        # The project: myaicofounder.com
        # Tagline: an always available AI co-founder that you can trust
        # Description: My AI Co-founder is an AI-powered SaaS product that gives entrepreneurs an AI co-founder that can help them build their business.
        # The AI co-founder can help with everything from product development to marketing and sales.
        # Current status: The product is still in idea phase and is looking to launch an early alpha soon.
        # Roadmap ideas:
        # * Give the user the ability to customize their AI co-founder's personality
        # * Teach the co-founder about various topics based on blogs, podcasts, and YouTube channels.
        # * Give the co-founder the ability to learn from the user's interactions with it.
        # * Provide the co-founder with a way to learn from the user's interactions with it.
        # * Evaluate the co-founder's performance in a number of important areas and suggest ways to improve it.
        # """
        print("Responding...")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                            {self.base_system_message}
                           Here's what your cofounder wants to know:
                            {message}

                           You thought about it and this is your conclusion: 
                           {thoughts}
                           
                           Here's what you remember from what you've learned so far:
                            {memories}

                           Now you need to respond to the message.
                           """),
            # The persistent system prompt
            MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
            HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
        ])
        chat_llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True,
            memory=self.memory,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        cofounder_response = chat_llm_chain.predict(
            human_input=message,
        )

        return cofounder_response

    def analyze_business_idea(self, idea):
        url = ""

    def update_current_knowledge(self):
        # reload from mongo and update the system message
        what_you_know = self.mongo_client.cofounder.business.find_one({"_id": ObjectId(self.business_id)})
        self.base_system_message = f"""
                 {self.profile}

                                           You are speaking to your co-founder, {self.founder_name}. {self.founder_profile}



                                           You are a cofounder of {self.business_name}.
                                           Here are the details about about the business:
                                           {self.business_profile}

                                            Here's what you know about the business:
                                            ##BUSINESS_NAME##
                                            {what_you_know['name']}
                                            ##END_BUSINESS_NAME##
                                            ##WEBSITE##
                                            {what_you_know['website']}
                                            ##END_WEBSITE##
                                            ##PROFILE##
                                            {what_you_know['profile']}
                                            #END_PROFILE#
                                            ##QUESTIONS_ABOUT_THE_BUSINESS##
                                            {what_you_know['questions']}
                                            ##END_QUESTIONS_ABOUT_THE_BUSINESS##
                                            #LEARNED_KNOWLEDGE#
                                            {what_you_know['knowledge']}
                                            #END_LEARNED_KNOWLEDGE#

                                           """

    def learn_about_the_business(self, message):
        self.question_the_business()
        self.update_current_knowledge()
        template = f"""
        {self.base_system_message}
        
        
        Here's the message from your cofounder:
        {{message}}
        
        Based on the questions you have, update the knowledge you have about the business and remove the questions you answer.
        Return the updated questions and knowledge in the following JSON format:
        
        {{{{
            "knowledge": "<knowledge>",
            "questions": "<questions>"
        }}}}
        
        
        """
        prompt = PromptTemplate(
            input_variables=["message"],
            template=template
        )
        chat_llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True,
        )
        reply = chat_llm_chain.predict(
            message=message,
        )
        parsed = json.loads(reply, strict=False)
        updated_knowledge = parsed['knowledge']
        questions = parsed['questions']

        self.mongo_client.cofounder.business.update_one({"_id": ObjectId(self.business_id)}, {
            "$set": {"knowledge": updated_knowledge, "questions": questions}})
        self.update_current_knowledge()

    def question_the_business(self):

        template = f"""
        {self.base_system_message}

        {{message}}
    
        """
        prompt = PromptTemplate(
            input_variables=["message"],
            template=template
        )
        chat_llm_chain = LLMChain(
            llm=self.llm,
            prompt=prompt,
            verbose=True,
        )
        reply = chat_llm_chain.predict(
            message="Given the current questions you have about the business and what you know, update the questions with any more questions you want to ask. Respond with the updated questions in the following JSON format: {{{{\"questions\": \"<questions>\"}}}}",
        )
        parsed = json.loads(reply, strict=False)
        questions = parsed['questions']
        self.mongo_client.cofounder.business.update_one({"_id": ObjectId(self.business_id)},
                                                        {"$set": {"questions": questions}})

    def learn(self, title, description, fulltext):
        source = Source()
        source.name = title
        source.description = description
        source.owner_id = self.user_id
        fulltext_id = str(uuid.uuid4())
        source.fulltext_id = fulltext_id
        source.save()
        self.db.fulltext.insert_one({"text": fulltext, "fulltext_id": fulltext_id})
        # first, we need to vectorize the title and description for the knowledge card.
        texts = [
            f'''
            {title}
            
            {description}
            
            '''
        ]
        ids = [
            str(uuid4())
        ]
        metadatas = [
            {
                "title": title,
                "description": description,
                "userId": self.user_id,
                'added': datetime.now().strftime("%Y-%m-%d"),
                "fulltext_id": source.id,
            }
        ]

        self.vectordb_cards.add_texts(texts, metadatas, ids)

        # then, we need to vectorize the fulltext for the knowledge text.
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=20,
            length_function=len,
            is_separator_regex=False,
        )
        chunks = text_splitter.split_text(fulltext)
        chunk_ids = [str(uuid4()) for _ in chunks]
        chunk_metadatas = [
            {
                "title": title,
                "description": description,
                "userId": self.user_id,
                'added': datetime.now().strftime("%Y-%m-%d"),
                "fulltext_id": source.id,
            } for _ in chunks
        ]
        self.vectordb_knowledge.add_texts(chunks, chunk_metadatas, chunk_ids)


    def remember(self, message):
        return self.memory_agent.remember(message)
