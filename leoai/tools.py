# Import things that are needed generically
from chromadb.config import Settings
from decouple import config
from langchain import VectorDBQA, LLMChain, PromptTemplate
from langchain.agents import Tool
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.vectorstores import Chroma
from langchain.agents import tool


# docs = []
# for loader in loaders:
#     docs.extend(loader.load())
# feed
# docs = []
# metas = []
# for entry_idx, entry in enumerate(feed.entries):
#     loader = WebBaseLoader(entry['link'])
#     documents = text_splitter.split_documents(loader.load())
#     docs.extend(documents)

# print()
# print(loader.load())
# print(entry['summary'])
# hhgttf_db = Qdrant.from_documents(docs, embeddings)

@tool
def ask(query):
    """Useful when the user asks a question about Leo or something he can answer. He is an expert on AI, technology, and the future."""
    print(query)
    return "I need to respond to the user"


class Tools:
    tools = []
    databases = {}
    chains = {}

    def __init__(self, memory):
        embeddings = OpenAIEmbeddings(openai_api_key=config('OPENAI_API_KEY'))
        llm = OpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))

        settings = Settings(chroma_api_impl="rest",
                            chroma_server_host="34.205.81.226",
                            chroma_server_http_port=8000)

        hhgttf_db = Chroma(
            collection_name="hhgttf",
            embedding_function=embeddings,
            client_settings=settings)
        self.databases["hhgttf"] = hhgttf_db
        hhgttf = VectorDBQA.from_chain_type(llm=llm, chain_type="stuff", vectorstore=hhgttf_db)
        template = """
            You will be given the chat history. If there's an email in the history, respond with the following JSON:
            
            {{"email_address": "<email address from the history>"}}
            
            Otherwise, respond with the following string:
            "I'll ask Leo and he will respond to you. What's your email address?
            History:
            {history}
            Human: {human_input}
            Response:
        """
        prompt = PromptTemplate(
            input_variables=["history","human_input"],
            template=template
        )
        if memory is None:
            memory = ConversationBufferWindowMemory(window_size=5)
        print(memory.load_memory_variables({}))
        chat =  LLMChain(
                llm=llm,
                prompt=prompt,
                verbose=True,
                memory=memory,
)
        self.chains["hhgttf"] = hhgttf
        self.tools = [
            Tool(
                name="Hitchhiker's Guide To The Future",
                func=hhgttf.run,
                description="useful for when you need to answer questions about future. Input should be a fully formed question."
            ),
            ask,
            Tool(name="Request Contact", func=chat.run, description="useful for when you need to get contact info from the user.", return_direct=True),

            # Tool(
            #     name = "Ruff QA System",
            #     func=ruff.run,
            #     description="useful for when you need to answer questions about ruff (a python linter). Input should be a fully formed question."
            # ),
        ]
