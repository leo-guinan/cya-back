import json
import logging
from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict, HumanMessage, AIMessage, SystemMessage, FunctionMessage, ToolMessage, ChatMessage,
)
from pymongo import MongoClient, errors

logger = logging.getLogger(__name__)

DEFAULT_DBNAME = "chat_history"
DEFAULT_COLLECTION_NAME = "message_store"


class MongoDBChatMessageHistoryOverride(BaseChatMessageHistory):
    """Chat message history that stores history in MongoDB.

    Args:
        connection_string: connection string to connect to MongoDB
        session_id: arbitrary key that is used to store the messages
            of a single chat session.
        database_name: name of the database to use
        collection_name: name of the collection to use
    """

    def __init__(
        self,
        connection_string: str,
        session_id: str,
        database_name: str = DEFAULT_DBNAME,
        collection_name: str = DEFAULT_COLLECTION_NAME,
    ):
        print(f'connection_string: {connection_string}')
        print(f'session_id: {session_id}')
        print(f'database_name: {database_name}')
        print(f'collection_name: {collection_name}')
        self.connection_string = connection_string
        self.session_id = session_id
        self.database_name = database_name
        self.collection_name = collection_name

        try:
            self.client: MongoClient = MongoClient(connection_string)
        except errors.ConnectionFailure as error:
            logger.error(error)

        self.db = self.client[database_name]
        self.collection = self.db[collection_name]
        self.collection.create_index("sessionId")

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from MongoDB"""
        try:
            cursor = self.collection.find({"sessionId": self.session_id})
        except errors.OperationFailure as error:
            logger.error(error)

        try:
            # Attempt to get the first document from the cursor
            document = next(cursor, None)
        except StopIteration:
            logger.info("No documents found for this session.")
            document = None

        if document and "messages" in document:
            items = document["messages"]
        else:
            items = []

        messages = messages_from_dict(items)
        return messages

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in MongoDB"""
        try:
            messages = [message]

            self.collection.update_one(
                {"sessionId": self.session_id},
                {
                    "$push": {
                        "messages": {
                            "$each": [message_to_dict(message) for message in messages],
                        }
                    }
                },
                upsert=True,
            )
        except errors.WriteError as err:
            logger.error(err)

    def clear(self) -> None:
        """Clear session memory from MongoDB"""
        try:
            self.collection.delete_many({"sessionId": self.session_id})
        except errors.WriteError as err:
            logger.error(err)

    def get_session_history(self):
        pass

