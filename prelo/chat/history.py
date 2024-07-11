from decouple import config

from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride


def get_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("SCORE_MY_DECK_DATABASE_NAME"),
        collection_name=config("SCORE_MY_DECK_COLLECTION_NAME")
    )


def get_prelo_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("PRELOVC_DATABASE_NAME"),
        collection_name=config("PRELOVC_COLLECTION_NAME")
    )
