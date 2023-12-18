import json

from decouple import config
from pymongo import MongoClient

from backend.celery import app
from cofounder.models import User as CofounderUser, ChatSession
from mail.service import send_email


@app.task(name="metrics.tasks.send_weekly_metrics")
def send_weekly_metrics():
    # cofounder metrics
    cofounder_user_count = CofounderUser.objects.count()
    metrics = {
        "users": cofounder_user_count,

    }
    combined_metrics = {}
    total_sessions = 0
    total_human_messages = 0
    for cofounder_user in CofounderUser.objects.all():
        cofounder_chat_session_messages = {}
        # get all chat sessions for user
        cofounder_chat_sessions = ChatSession.objects.filter(user=cofounder_user).all()
        chat_session_count = cofounder_chat_sessions.count()
        #get_number_of_messages_for_each_session
        mongo_client = MongoClient(config('MONGODB_CONNECTION_STRING'))
        db = mongo_client.chat_history
        for cofounder_chat_session in cofounder_chat_sessions:
            messages = [message for message in db.message_store.find({"SessionId": cofounder_chat_session.session_id})]
            total_messages = len(messages)
            ai_messages = len([message for message in messages if json.loads(message['History'])['type'] == 'ai'])
            human_messages = len([message for message in messages if json.loads(message['History'])['type'] == 'human'])
            cofounder_chat_session_messages[cofounder_chat_session.session_id] = {
                "total_messages": total_messages,
                "ai_messages": ai_messages,
                "human_messages": human_messages
            }
            total_sessions += 1
            total_human_messages += human_messages
        combined_metrics[cofounder_user.name] = {
            "chat_session_count": chat_session_count,
            "chat_session_messages": cofounder_chat_session_messages
        }
    metrics["total_messages_sent"] = total_human_messages
    metrics["messages_per_chat"] = total_human_messages / total_sessions
    send_email(to=config("METRICS_EMAIL"), subject="Weekly Metrics", message=json.dumps(metrics))



