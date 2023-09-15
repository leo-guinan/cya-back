from asgiref.sync import async_to_sync

from coach.characters.alix import Alix
from coach.models import ChatCredit


def run_daily_bad_chat(session, message, user, channel_layer):
    async_to_sync(channel_layer.group_send)(session.session_id,
                                            {"type": "chat.message", "message": "Thinking...", "id": -1})

    alix = Alix(session.session_id, user.id, """Your client isn't feel good today about their business.  They are feeling down and need some encouragement.
                    Ask questions to understand what's going on be supportive.""")

    response = alix.respond_to_message(message)

    # record chat credit used
    chat_credit = ChatCredit(user=user, session=session)
    chat_credit.save()
    # print(alix_response)

    # need to send message to websocket
    async_to_sync(channel_layer.group_send)(session.session_id,
                                            {"type": "chat.message", "message": response, "id": -1})
