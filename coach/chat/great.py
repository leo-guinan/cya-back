from asgiref.sync import async_to_sync
from decouple import config
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from coach.models import ChatCredit


def run_daily_great_chat(session, message, user, channel_layer):
    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session.session_id
    )
    llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                     openai_api_base=config('OPENAI_API_BASE'), headers={
            "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
        })
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=f"""
                    You are Alix, the Build In Public Coach. You are friendly, informal, and tech-savvy.

                    Your client is feeling great today about their business.  They are feeling good and want to share their success with you.
                    Ask questions to understand what's going on and be supportive.
                    Help them celebrate what's going well.
                    """),
        # The persistent system prompt
        MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
        HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
    ])

    print(prompt)
    async_to_sync(channel_layer.group_send)(session.session_id,
                                            {"type": "chat.message", "message": "Thinking...", "id": -1})

    alix_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,
                                           chat_memory=message_history)

    chat_llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True,
        memory=alix_memory,
    )

    # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

    alix_response = chat_llm_chain.predict(
        human_input=message,
    )

    # record chat credit used
    chat_credit = ChatCredit(user=user, session=session)
    chat_credit.save()
    # print(alix_response)
    # need to send message to websocket
    async_to_sync(channel_layer.group_send)(session.session_id,
                                            {"type": "chat.message", "message": alix_response, "id": -1})