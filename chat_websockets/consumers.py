import json
from django.core.cache import cache
import hashlib

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from agi.tasks import respond_to_agi_message
from cli.tasks import run_command
from coach.tasks import respond_to_chat_message
from cofounder.tasks import respond_to_cofounder_message
from prelo.models import MessageToConfirm
from toolkit.tasks import youtube_to_blog, idea_collider
from prelo.tasks import acknowledge_received, acknowledged_analyzed, acknowledged_created

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
            if text_data_json['type'] == 'acknowledged_analyzed':
                acknowledged_analyzed.delay(self.session, text_data_json['deck_uuid'], text_data_json['report_uuid'])
            elif text_data_json['type'] == 'acknowledge_received':
                acknowledge_received.delay(self.session, text_data_json['deck_uuid'])
            elif text_data_json['type'] == 'acknowledge_created':
                acknowledged_created.delay(self.session)
        elif self.app == 'toolkit':
            print(f"toolkit received: {text_data}")
            if text_data_json["type"] == "idea_collider":
                video_url = text_data_json["youtube_url"]
                other_youtube_video_url = text_data_json["other_youtube_url"]
                intersection = text_data_json["intersection"]
                audience = text_data_json["audience"]
                idea_collider.delay(video_url, other_youtube_video_url, intersection, audience, self.session)
            elif text_data_json["type"] == "video_to_blog":
                youtube_url = text_data_json["youtube_url"]
                audience = text_data_json["audience"]
                youtube_to_blog.delay(youtube_url, audience, self.session)

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
        pitch_deck_analysis = event["pitch_deck_analysis"]
        scores = event["scores"]
        self.send(text_data=json.dumps({"top_concern": top_concern, "objections": objections,
                                        "how_to_overcome": how_to_overcome,
                                        "pitch_deck_analysis": pitch_deck_analysis,
                                        "scores": scores}))

    def write_blog(self, event):
        outline = event["outline"]
        post = event["post"]
        title = event["title"]
        self.send(text_data=json.dumps({"outline": outline, "post": post, "title": title}))

    def idea_collider(self, event):
        result = event["result"]
        self.send(text_data=json.dumps({"result": result, }))

    def deck_received(self, event):
        deck_uuid = event["deck_uuid"]
        message_content = json.dumps({"deck_uuid": deck_uuid, "status": "received"})
        MessageToConfirm.objects.create(message=json.dumps(event), type="deck_received",
                                        conversation_uuid=self.session, deck_uuid=deck_uuid)
        self.send(text_data=message_content)

    def deck_analyzed(self, event):
        deck_uuid = event["deck_uuid"]
        deck_score = event["deck_score"]
        recommended_next_steps = event["recommended_next_steps"]
        report_summary = event["report_summary"]
        report_uuid = event["report_uuid"]
        company_name = event["company_name"]
        message_content = json.dumps({
            "deck_uuid": deck_uuid,
            "status": "analyzed",
            "deck_score": deck_score,
            "recommended_next_steps": recommended_next_steps,
            "report_summary": report_summary,
            "report_uuid": report_uuid,
            "company_name": company_name
        })
        MessageToConfirm.objects.create(message=json.dumps(event), type="deck_analyzed",
                                        conversation_uuid=self.session,
                                        deck_uuid=deck_uuid, report_uuid=report_uuid)
        self.send(text_data=message_content)

    def submind_created(self, event):
        # Create a unique hash for this event
        event_hash = hashlib.md5(json.dumps(event, sort_keys=True).encode()).hexdigest()
        cache_key = f"submind_created:{event_hash}"

        # Check if we've processed this event before
        if not cache.get(cache_key):
            submind_id = event["submind_id"]
            investor_id = event["investor_id"]
            firm_id = event["firm_id"]
            thesis = event["thesis"]
            passion = event["passion"]
            check_size = event["check_size"]
            industries = event["industries"]
            slug = event["slug"]
            company = event["company"]
            name = event["name"]
            message_content = json.dumps({
                "submind_id": submind_id,
                "investor_id": investor_id,
                "firm_id": firm_id,
                "status": "configured",
                "thesis": thesis,
                "passion": passion,
                "check_size": check_size,
                "industries": industries,
                "slug": slug,
                "company": company,
                "name": name
            })
            MessageToConfirm.objects.create(message=json.dumps(event), type="submind_created",
                                            conversation_uuid=self.session)
            self.send(text_data=message_content)

            # Mark this event as processed
            cache.set(cache_key, True, timeout=3600)  # Cache for 1 hour
        else:
            print(f"Duplicate submind_created event ignored: {event_hash}")
