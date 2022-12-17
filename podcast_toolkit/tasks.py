import json

from backend.celery import app
from podcast_toolkit.models import Podcast
from transformer.service import transform_podcast_transcript, create_embeddings_for_podcast_transcript
from webhooks.models import TranscriptRequestEmail


@app.task(name="podcast_toolkit.process_transcript_request")
def process_transcript_request(request_id):
    request = TranscriptRequestEmail.objects.filter(id=request_id).first()
    if request is not None:
        if not request.processed:
            embeddings = create_embeddings_for_podcast_transcript(request.transcript)
            podcast = Podcast(title=request.title, transcript=request.transcript)
            podcast.save()
            summary, key_points, links_to_include = transform_podcast_transcript(request.transcript)
            podcast.summary = summary
            podcast.key_points = key_points
            podcast.links_to_include = links_to_include
            podcast.transcript_embeddings = json.dumps(embeddings)
            podcast.save()
            request.processed = True
            request.save()
