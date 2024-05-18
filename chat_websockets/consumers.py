import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer

from agi.tasks import respond_to_agi_message
from cli.tasks import run_command
from coach.tasks import respond_to_chat_message
from cofounder.tasks import respond_to_cofounder_message


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        self.session = self.scope["url_route"]["kwargs"]["session_id"]
        self.app = self.scope["url_route"]["kwargs"]["app"]
        self.session_group_name = f"{self.session}"

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
    def receive(self, text_data, **kwargs):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        if self.app == 'cofounder':
            respond_to_cofounder_message.delay(message, text_data_json['user_id'], self.session)
        elif self.app == 'agi':
            respond_to_agi_message.delay(message, text_data_json['user_id'], self.session)
        elif self.app == 'cli':
            run_command.delay(message, self.session)
        elif self.app == 'prelo':
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(self.session,
                                                    {"type": "chat.message", "message": "message received",
                                                     "id": "state"})

        else:
            respond_to_chat_message.delay(message, text_data_json['user_id'], self.session)

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]
        message_id = event["id"]
        # Send message to WebSocket
        self.send(text_data=json.dumps({"message": message, "id": message_id}))

    def deck_status_update(self, event):
        message = event["message"]
        message_id = event["id"]
        status = event["status"]
        self.send(text_data=json.dumps({"message": message, "id": message_id, "status": status}))

    def deck_recommendation(self, event):
        message_id = event["id"]
        concerns = event["concerns"]
        believe = event["believe"]
        traction = event["traction"]
        summary = event["summary"]
        recommendation_score = event["recommendation_score"]
        if recommendation_score > 70:
            recommendation = "contact"
        elif recommendation_score > 50:
            recommendation = "maybe"
        else:
            recommendation = "pass"
        recommendation_reasons = event["recommendation"]
        self.send(text_data=json.dumps({"id": message_id,
                                        "concerns": concerns,
                                        "believe": believe,
                                        "traction": traction,
                                        "summary": summary,
                                        "recommendation": recommendation,
                                        "recommendation_reasons": recommendation_reasons}))


    def deck_score_update(self, event):
        message = event["message"]
        message_id = event["id"]
        scores = event["scores"]
        self.send(text_data=json.dumps({"message": message, "id": message_id, "scores": scores}))

    def deck_report_update(self, event):
        top_concern = event["top_concern"]
        objections = event["objections"]
        how_to_overcome = event["how_to_overcome"]
        scores = event["scores"]
        self.send(text_data=json.dumps({"top_concern": top_concern, "objections": objections,
                                        "how_to_overcome": how_to_overcome, "scores": scores}))