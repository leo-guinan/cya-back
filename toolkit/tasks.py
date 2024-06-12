from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config

from backend.celery import app
import requests
import time


def make_fetch_request(url, headers, method='GET', data=None):
    if method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    else:
        response = requests.get(url, headers=headers)
    return response.json()





@app.task(name='toolkit.tasks.youtube_to_blog')
def youtube_to_blog(video_url, audience, ws_uuid):
    gladia_key = config('GLADIA_API_KEY')
    request_data = {
        "audio_url": "https://www.youtube.com/watch?v=1CGlGcQMF8Y",
        "diarization": True,

    }
    gladia_url = "https://api.gladia.io/v2/transcription/"

    headers = {
        "x-gladia-key": gladia_key,
        "Content-Type": "application/json"
    }

    print("- Sending initial request to Gladia API...")
    initial_response = make_fetch_request(
        gladia_url, headers, 'POST', request_data)

    print("Initial response with Transcription ID:", initial_response)
    result_url = initial_response.get("result_url")

    if result_url:
        while True:
            print("Polling for results...")
            poll_response = make_fetch_request(result_url, headers)

            if poll_response.get("status") == "done":
                print("- Transcription done: \n")
                transcript = poll_response.get("result", {}).get("transcription", {"full_transcript: """})['full_transcript']




                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(ws_uuid, {
                    "type": "write.blog",
                    "message": transcript,
                })
                break
            else:
                print("Transcription status:", poll_response.get("status"))
            time.sleep(1)
