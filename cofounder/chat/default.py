from asgiref.sync import async_to_sync

from cofounder.cofounder.default import DefaultCofounder
from cofounder.models import ChatCredit, ChatError
from cofounder.tools.fix_json import FixJSONTool


def run_default_chat(session, message, user, channel_layer):
    fix_json_tool = FixJSONTool()

    try:

        alix = DefaultCofounder(session.session_id, user.id)

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
                                                                     "message": "Sorry, there was an error processing your request. Please try again.",
                                                                     "id": -1})
