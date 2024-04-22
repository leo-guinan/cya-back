import uuid
from functools import partial

import pinecone
import requests
from decouple import config
from langchain.agents import LLMSingleActionAgent, AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.vectorstores import Pinecone
from langchain.tools import Tool as LangchainTool
from langchain_community.chat_message_histories import MongoDBChatMessageHistory
from langchain_community.chat_models import ChatOpenAI
from langchain_community.tools.render import format_tool_to_openai_function
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import MessagesPlaceholder, ChatPromptTemplate
from pymongo import MongoClient

from agi.models import Person, Tool, OutgoingRequest
from agi.templates.custom_output_parser import CustomOutputParser
from agi.templates.custom_prompt import CustomPromptTemplate


class Agent:
    def __init__(self, session_id):
        self.people = Person.objects.all()
        self.tools = Tool.objects.all()
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
        self.vectorstore_tools = Pinecone(index, embeddings.embed_query, "text", namespace="agi_tools")
        self.vectorstore_people = Pinecone(index, embeddings.embed_query, "text", namespace="agi_people")

        self.tool_retriever = self.vectorstore_tools.as_retriever()
        self.people_retriever = self.vectorstore_people.as_retriever()
        self.llm = ChatOpenAI(temperature=0, api_key=config('OPENAI_API_KEY'), model_name="gpt-4-turbo", )

        self.mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.agi
        self.message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )

    def determine_action(self, message):
        template = """Break down the steps required to answer the provided question. 
        
        Sometimes, you will have to wait on a response. In that case, stop answering the question and once the response is received, you can pick up where you left off.
        
        You can use the following tools: 

        {tools}

        Use the following format:

        Question: the input question you must answer
        Thought: you should always think about what to do
        Action: the action to take, should be one of [{tool_names}]
        Action Input: the input to the action
        Observation: the result of the action
        ... (this Thought/Action/Action Input/Observation can repeat N times)
        Thought: I now know the final answer
        Final Answer: the final answer to the original input question
        
        Here's your conversation so far:
        {conversation_history}

        Begin!

        Question: {input}
        {agent_scratchpad}"""

        prompt = CustomPromptTemplate(
            template=template,
            tools=self.get_tools("This is a sample message"),
            conversation_history=self.message_history.messages,
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"],
        )

        MEMORY_KEY = "chat_history"


        # LLM chain consisting of the LLM and a prompt
        llm_chain = LLMChain(llm=self.llm, prompt=prompt)
        output_parser = CustomOutputParser()
        tool_names = [t.name for t in self.get_tools("This is a sample message")]
        # prompt = CustomPromptTemplate(
        #     template=template,
        #     tools=self.get_tools("This is a sample message"),
        #     # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
        #     # This includes the `intermediate_steps` variable because that is needed
        #     input_variables=["input", "intermediate_steps"]
        # )
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=tool_names
        )

        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=self.get_tools("This is a sample message"), verbose=True)

        result = agent_executor.run(message)
        print(result)
        self.message_history.add_message(HumanMessage(content=message))
        self.message_history.add_message(AIMessage(content=result))

        return result



    def get_tools(self, query):
        docs = self.tool_retriever.get_relevant_documents(query)
        all_tools = []
        for d in docs:
            matched_tool = self.tools.get(id=d.metadata["tool_id"])
            created_tool = LangchainTool(
                name=matched_tool.name,
                func=partial(self.use_tool, "tool", matched_tool.id),
                description=f"useful for when you need to {matched_tool.name}",
            )
            all_tools.append(created_tool)


        people = self.get_people(query)
        for person in people:
            created_tool = LangchainTool(
                name=person.name,
                func=partial(self.use_tool, "person", person.id),
                description=f"useful for when you need information about {person.description}",
            )
            all_tools.append(created_tool)

        all_tools.append(LangchainTool(
            name="Wait",
            func=self.wait_for_response,
            description="Useful when you need to wait for a response from a tool or a person",
        ))
        return all_tools


    def get_people(self, query):
        docs = self.people_retriever.get_relevant_documents(query)
        return [self.people.get(id=d.metadata["person_id"]) for d in docs]

    def use_tool(self, tool_type, tool_id, message):
        uuid_id = str(uuid.uuid4())
        webhook_url = f"http://localhost:8000/api/agi/webhook/{uuid_id}"
        outgoing_webhook = OutgoingRequest()
        outgoing_webhook.message = message
        outgoing_webhook.webhook_url = webhook_url
        outgoing_webhook.uuid = uuid_id
        outgoing_webhook.respond_to = "me"
        outgoing_webhook.save()

        if tool_type == "tool":
            tool = self.tools.get(id=tool_id)
            requests.post(tool.url, json={"message": message, "respond_to": webhook_url})
        elif tool_type == "person":
            person = self.people.get(id=tool_id)
            requests.post(person.url, json={"message": message, "respond_to": webhook_url})
        else:
            raise Exception("Invalid tool type")

    def wait_for_response(self, message):
        return "Request has been sent. The answer will be sent when it is available. That is the final answer."