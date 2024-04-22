from decouple import config
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import MongoDBChatMessageHistory
from langchain_community.chat_models import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate


def generate_document_from_prompt(prompt, uuid):
    internal_message_history = MongoDBChatMessageHistory(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'), session_id=f"document_generate_{uuid}"
    )
    internal_memory = ConversationBufferMemory(memory_key="chat_history", chat_memory=internal_message_history,
                                               return_messages=True)
    llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4-turbo",
                     )
    prompt_from_messages = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""
        You are a plan of action generator. Given a user's intent, and a few related thoughts, your job
        is to generate a markdown action plan that includes as much detail as possible to help the user quickly and completely
        complete their task.        
        """),
        # The persistent system prompt
        MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
        HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
    ])
    chat_llm_chain = LLMChain(
        llm=llm,
        prompt=prompt_from_messages,
        verbose=True,
        memory=internal_memory,
    )

    # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

    response = chat_llm_chain.predict(
        human_input=prompt,
    )

    return response
