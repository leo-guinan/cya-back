from decouple import config
from langchain import LLMChain
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.prompts import MessagesPlaceholder, HumanMessagePromptTemplate, ChatPromptTemplate
from langchain.schema import SystemMessage
from langchain.tools import Tool

from coach.tools.background import BackgroundTool


class Alix:
    def __init__(self, session_id, user_id):
        self.session_id = session_id
        self.user_id = user_id
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )
        internal_message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=f"internal_{session_id}"
        )

        self.memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=message_history, input_key="human_input", return_messages=True)
        self.internal_memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=internal_message_history, return_messages=True)
        self.llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                              openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })

    def think_about_the_message(self, message):
        tools = [
            Tool(
                name="Intermediate Answer",
                func=self._consult_client_records,
                description="useful for when you need to look up information about the client",
            )
        ]

        agent_chain = initialize_agent(tools, self.llm, agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION, verbose=True,
                                       memory=self.internal_memory)

        return agent_chain.run(
            input=message
        )

    def _consult_client_records(self, query):
        return BackgroundTool(self.user_id).answer_question(query)

    def ask_research_assistant(self, question):
        pass

    def respond_to_message(self, message):
        thoughts = self.think_about_the_message(message)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                        You are Alix, the Build In Public Coach. You are friendly, informal, and tech-savvy.

                        You believe that building in public is a great way to empower people to build their own businesses.

                        You are supportive, encouraging, and helpful.

                        You are a great listener and you are always looking for ways to help your clients.
                        
                        You thought about the message and this is your conclusion: {thoughts}
                        
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

        alix_response = chat_llm_chain.predict(
            human_input=message,
        )
        print(alix_response)

        return alix_response
