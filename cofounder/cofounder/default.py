from decouple import config
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from coach.tools.background import BackgroundTool
from cofounder.models import Cofounder, BusinessProfile, FounderProfile, User

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
        self.base_system_message = f"""
         {self.profile}

                                   You are speaking to your co-founder, {self.founder_name}. {self.founder_profile}

                                   

                                   You are a cofounder of {self.business_name}.
                                   Here are the details about about the business:
                                   {self.business_profile}

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
        self.llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                              openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })

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
            memory=self.memory,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        cofounder_response = chat_llm_chain.predict(
            human_input=message,
        )
        print(cofounder_response)
        return cofounder_response

    def _consult_client_records(self, query):
        return BackgroundTool(self.user_id).answer_question(query)

    def ask_research_assistant(self, question):
        pass

    def respond_to_message(self, message):
        thoughts = self.think_about_the_message(message)
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
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                            {self.base_system_message}
                           Here's what your cofounder wants to know:
                            {message}

                           You thought about it and this is your conclusion: {thoughts}

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
        print(cofounder_response)

        return cofounder_response

    def analyze_business_idea(self, idea):
        url = ""
