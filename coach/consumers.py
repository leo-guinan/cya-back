import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from coach.tasks import respond_to_chat_message

class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.session = self.scope["url_route"]["kwargs"]["session_id"]
        self.session_group_name = f"chat_{self.session}"

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.session_group_name, self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.session_group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        print(message)
        # Send message to room group
        respond_to_chat_message.delay(message, text_data_json['user_id'], self.session_group_name)

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message}))