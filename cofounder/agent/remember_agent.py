import json

import pinecone
from decouple import config
from langchain.agents import AgentExecutor, LLMSingleActionAgent
from langchain.chains import LLMChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.tools import Tool
from langchain.vectorstores import Pinecone
from pymongo import MongoClient

from cofounder.agent.remember_output_parser import RememberParser
from cofounder.agent.remember_template import RememberTemplate
from cofounder.models import Source
from cofounder.tools.source import SourceTool


class RememberAgent:

    def __init__(self, user_id):
        self.user_id = user_id
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
        self.vectorstore = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source_cards")
        self.vectorstore_knowledge = Pinecone(index, embeddings.embed_query, "text", namespace="cofounder_source")

        self.tool_retriever = self.vectorstore.as_retriever()
        self.llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4-turbo",)

        self.mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
        self.db = self.mongo_client.cofounder
        self.all_tools = Source.objects.filter(owner__id=self.user_id).all()
        print(len(self.all_tools))


    def _get_tools(self, input):


        # self.db.fulltext.insert_one({"text": fulltext, "fulltext_id": fulltext_id})

        docs = self.tool_retriever.get_relevant_documents(input)
        print(docs)
        matched_tools = []
        for doc in docs:
            print("doc", doc.metadata['fulltext_id'])
            for tool in self.all_tools:
                print("tool", tool)
                print("equal", tool.id == doc.metadata['fulltext_id'])
                if tool.id == doc.metadata['fulltext_id']:
                    print("matched, building tool")
                    print(tool.name)
                    built_tool = SourceTool(self.user_id)
                    print(built_tool)
                    matched_tools.append(Tool(
                        name=tool.name,
                        description=tool.description,
                        func=built_tool.answer_question

                    ))


        # ids = self.all_tools.map(lambda t: )
        # for doc in docs:
        #     if self.all_toolsdoc.metadata['fullText_id']
        print(matched_tools)
        return matched_tools
    def remember(self, message):
        template = """Think about what you need to know in order to respond to your cofounder. You have access to the following tools:

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

        Begin! Remember to speak to your cofounder in a friendly, informal, and tech-savvy way.

        Question: {input}
        {agent_scratchpad}"""

        tools = self._get_tools(message)

        output_parser = RememberParser()
        prompt = RememberTemplate(
            template=template,
            tools_getter=self._get_tools,
            # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
            # This includes the `intermediate_steps` variable because that is needed
            input_variables=["input", "intermediate_steps"],
        )

        llm_chain = LLMChain(llm=self.llm, prompt=prompt)

        tool_names = [tool.name for tool in tools]
        print(tool_names)
        agent = LLMSingleActionAgent(
            llm_chain=llm_chain,
            output_parser=output_parser,
            stop=["\nObservation:"],
            allowed_tools=tool_names,
        )

        agent_executor = AgentExecutor.from_agent_and_tools(agent=agent, tools=tools, verbose=True)
        return agent_executor.run(input=message)
