import time

import requests
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from langchain_community.output_parsers.ernie_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate

from backend.celery import app
from submind.llms.submind import SubmindModelFactory


def make_fetch_request(url, headers, method='GET', data=None):
    if method == 'POST':
        response = requests.post(url, headers=headers, json=data)
    else:
        response = requests.get(url, headers=headers)
    return response.json()


BLOG_OUTLINE_PROMPT = """You are an expert at repurposing information. Given a transcript 
from a YouTube video and a desired audience, write an outline for a blog post based on the information in the transcript.



Finally, come up with an engaging title for the blog post.

Here's the transcript: {transcript}

Here's the audience: {audience}


"""

BLOG_POST_PROMPT = """
You are an expert at repurposing information. Given a transcript from a YouTube video, an outline, and a desired audience, 

write a blog post based on the information in the transcript.

Transcript: {transcript}
Outline: {outline}
Audience: {audience}
"""

BLOG_TITLE_PROMPT = """
You are an expert at repurposing information. Given a transcript from a YouTube video, a desired audience, 
and the post, write a compelling title for that blog post.

Transcript: {transcript}
Audience: {audience}
Post: {post}

"""

functions = [
    {
        "name": "write_blog_outline",
        "description": "write an outline for a blog post based on a youtube video transcript and a target audience",
        "parameters": {
            "type": "object",

            "properties": {
                "blog_outline": {
                    "type": "string",
                    "description": "The outline for the blog post",
                },

            }
        },

        "required": ["blog_outline"],
    },
    {
        "name": "write_blog_post",
        "description": "write a blog post for a given target audience based on a transcript and an outline",
        "parameters": {
            "type": "object",

            "properties": {
                "blog_post": {
                    "type": "string",
                    "description": "The blog post for the target audience",
                },

            }
        },

        "required": ["blog_post"],
    },
{
        "name": "write_blog_title",
        "description": "write a title for a blog post for a given target audience ",
        "parameters": {
            "type": "object",

            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title for the blog post",
                },

            }
        },

        "required": ["title"],
    },
]


@app.task(name='toolkit.tasks.youtube_to_blog')
def youtube_to_blog(video_url, audience, ws_uuid):
    gladia_key = config('GLADIA_API_KEY')
    request_data = {
        "audio_url": video_url,
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
    model = SubmindModelFactory.get_model(ws_uuid, "youtube_to_blog")
    outline_prompt = ChatPromptTemplate.from_template(BLOG_OUTLINE_PROMPT)
    outline_chain = outline_prompt | model.bind(function_call={"name": "write_blog_outline"},
                                functions=functions) | JsonOutputFunctionsParser()

    post_prompt = ChatPromptTemplate.from_template(BLOG_POST_PROMPT)
    post_chain = post_prompt | model.bind(function_call={"name": "write_blog_post"},
                                functions=functions) | JsonOutputFunctionsParser()

    title_prompt = ChatPromptTemplate.from_template(BLOG_TITLE_PROMPT)
    title_chain = title_prompt | model.bind(function_call={"name": "write_blog_title"},
                                functions=functions) | JsonOutputFunctionsParser()

    if result_url:
        while True:
            print("Polling for results...")
            poll_response = make_fetch_request(result_url, headers)

            if poll_response.get("status") == "done":
                print("- Transcription done: \n")
                transcript = poll_response.get("result", {}).get("transcription", {"full_transcript: """})[
                    'full_transcript']
                outline = outline_chain.invoke(
                    {"transcript": transcript,
                     "audience": audience

                     }
                )
                post = post_chain.invoke(
                    {"transcript": transcript,
                     "audience": audience,
                     "outline": outline.get("blog_outline", "")
                     }
                )

                title = title_chain.invoke(
                    {"transcript": transcript,
                     "audience": audience,
                     "post": post.get("blog_post", "")
                     }
                )

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(ws_uuid, {
                    "type": "write.blog",
                    "outline": outline.get("blog_outline"),
                    "post": post.get("blog_post"),
                    "title": title.get("title")
                })
                break
            else:
                print("Transcription status:", poll_response.get("status"))
            time.sleep(1)
