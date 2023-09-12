import json

from asgiref.sync import async_to_sync
from decouple import config
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from coach.characters.alix import Alix
from coach.models import ChatCredit, ChatError
from coach.tools.background import BackgroundTool
from coach.tools.chat_namer import ChatNamerTool
from coach.tools.coaching import CoachingTool
from coach.tools.fix_json import FixJSONTool
from coach.tools.lookup import LookupTool
from coach.tools.needed import WhatsNeededTool


def run_default_chat(session, message, user, channel_layer):
    fix_json_tool = FixJSONTool()


    try:
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": "Thinking...",
                                                 "id": -1})
        print(f"Message: {message}")

        alix = Alix(session.session_id, user.id)

        response = alix.respond_to_message(message)



        # record chat credit used
        chat_credit = ChatCredit(user=user, session=session)
        chat_credit.save()
        # print(alix_response)

    #     source_markdown = "\n\n".join(
    #         [f"""[{source.metadata['title']}]({source.metadata['url']})""" for source in document['source_documents']])
    #
    #     composite_response = f"""
    # {alix_response}
    #
    # Sources:
    #
    # {source_markdown}
    #         """

        # print(composite_response)
        # need to send message to websocket
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": response, "id": -1})
    except Exception as e:
        error = str(e)
        print(f'Error: {e}')
        chat_error = ChatError(error=error, session=session)
        chat_error.save()
        async_to_sync(channel_layer.group_send)(session.session_id, {"type": "chat.message",
                                                             "message": "Sorry, there was an error processing your request. Please try again.", "id": -1})
