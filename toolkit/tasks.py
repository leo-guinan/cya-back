import os
import time
import uuid
from datetime import datetime
from io import BytesIO

import chromadb
import requests
from PIL import Image
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from langchain_community.output_parsers.ernie_functions import JsonOutputFunctionsParser
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient

from backend.celery import app
from prelo.aws.s3_utils import upload_file_to_s3
from submind.llms.submind import SubmindModelFactory
from toolkit.models import YoutubeVideo, BlogPost, IdeaColliderOutput


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

IDEA_COLLIDER_THINKING_PROMPT = """
You are an idea generation submind. You take ideas from multiple places and combine them into something amazing at the specified intersection of ideas.

The first step is to understand the user's intent. Based on the intersection of ideas mentioned and the target audience,
figure out the intent of the user, and what questions you need to answer in order to provide the best possible output.

Intersection: {intersection}
Audience: {audience}

"""

IDEA_COLLIDER_LEARNING_PROMPT = """
You are an idea generation submind. You take ideas from multiple places and combine them into something amazing at the specified intersection of ideas.

Now you've figured out what the user intends and some questions you need to answer. 

Take the transcripts of the two videos and use those to answer the questions.

Intersection: {intersection}
Audience: {audience}
Intention: {intention}
Questions: {questions}
Transcript 1: {transcript_1}
Transcript 2: {transcript_2}

"""

IDEA_COLLIDER_CREATING_PROMPT = """
You are an idea generation submind. You take ideas from multiple places and combine them into something amazing at the specified intersection of ideas.

Now you've learned what you need to learn.

Now create what the user is looking for based on the intersection of ideas and the target audience.

Transcript 1: {transcript_1}
Transcript 2: {transcript_2}
Intersection: {intersection}
Audience: {audience}
Intention: {intention}
Questions: {questions}
Answers: {answers}

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
    {
        "name": "determine_intent_and_questions",
        "description": "based on a user's input, determine the user's intent and identify the questions that need to be answered",
        "parameters": {
            "type": "object",

            "properties": {
                "intent": {
                    "type": "string",
                    "description": "What the user wants you to create",
                },
                "questions": {
                    "type": "array",
                    "description": "The questions the you need to answer in order to create what the user is looking for",
                    "items": {
                        "type": "string"
                    }
                },

            }
        },

        "required": ["intent", "questions"],
    },
]


@app.task(name='toolkit.tasks.youtube_to_blog')
def youtube_to_blog(video_url, audience, ws_uuid):
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

    transcript = transcribe_youtube_video(video_url)
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
    BlogPost.objects.create(title=title.get("title"), content=post.get("blog_post"),
                            outline=outline.get("blog_outline"), uuid=str(uuid.uuid4()))

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(ws_uuid, {
        "type": "write.blog",
        "outline": outline.get("blog_outline"),
        "post": post.get("blog_post"),
        "title": title.get("title")
    })


@app.task(name='toolkit.tasks.idea_collider')
def idea_collider(video_url, other_youtube_video_url, intersection, audience, ws_uuid):
    transcript_1 = transcribe_youtube_video(video_url)
    transcript_2 = transcribe_youtube_video(other_youtube_video_url)

    model = SubmindModelFactory.get_model(ws_uuid, "youtube_to_blog")
    collider_prompt = ChatPromptTemplate.from_template(IDEA_COLLIDER_THINKING_PROMPT)
    collider_chain = collider_prompt | model.bind(function_call={"name": "determine_intent_and_questions"},
                                                  functions=functions) | JsonOutputFunctionsParser()

    result = collider_chain.invoke(
        {"intersection": intersection,
         "audience": audience
         }
    )

    collider_learning_prompt = ChatPromptTemplate.from_template(IDEA_COLLIDER_LEARNING_PROMPT)
    collider_learning_chain = collider_learning_prompt | model | StrOutputParser()

    answers = collider_learning_chain.invoke(
        {"intersection": intersection,
         "audience": audience,
         "intention": result.get("intent"),
         "questions": result.get("questions"),
         "transcript_1": transcript_1,
         "transcript_2": transcript_2
         }
    )

    collider_creating_prompt = ChatPromptTemplate.from_template(IDEA_COLLIDER_CREATING_PROMPT)
    collider_creating_chain = collider_creating_prompt | model | StrOutputParser()

    result = collider_creating_chain.invoke(
        {"intersection": intersection,
         "audience": audience,
         "intention": result.get("intent"),
         "questions": result.get("questions"),
         "transcript_1": transcript_1,
         "transcript_2": transcript_2,
         "answers": answers
         }
    )
    IdeaColliderOutput.objects.create(first_video=YoutubeVideo.objects.get(url=video_url),
                                      second_video=YoutubeVideo.objects.get(url=other_youtube_video_url),
                                      result=result, uuid=str(uuid.uuid4()))
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(ws_uuid, {
        "type": "idea.collider",
        "result": result
    })


def transcribe_youtube_video(video_url):
    existing_video = YoutubeVideo.objects.filter(url=video_url).first()
    if existing_video:
        return existing_video.transcript

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
    if result_url:
        while True:
            print("Polling for results...")
            poll_response = make_fetch_request(result_url, headers)

            if poll_response.get("status") == "done":
                print("- Transcription done: \n")
                transcript = poll_response.get("result", {}).get("transcription", {"full_transcript: """})[
                    'full_transcript']
                YoutubeVideo.objects.create(url=video_url, transcript=transcript)
                return transcript
            else:
                print("Transcription status:", poll_response.get("status"))
            time.sleep(1)


@app.task(name='toolkit.tasks.sync_google_docs')
def fetch_google_docs_data(tokens, user_id):
    print(tokens)
    creds = Credentials(
        client_id=config('GOOGLE_CLIENT_ID'),
        client_secret=config('GOOGLE_CLIENT_SECRET'),
        refresh_token=tokens['refresh_token'],
        token=tokens['access_token'],
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    )

    try:
        service = build('docs', 'v1', credentials=creds)
        drive_service = build('drive', 'v3', credentials=creds)

        page_token = None
        while True:
            # List Google Docs owned by the user, with pagination
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document' and 'me' in owners",
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                pageSize=100  # Adjust as needed
            ).execute()

            items = results.get('files', [])

            for item in items:
                process_single_doc.delay(tokens, item['id'], user_id)  # Kick off a sub-task for each doc

            page_token = results.get('nextPageToken')
            if not page_token:
                break  # No more pages
    except Exception as e:
        print(f"Error fetching Google Docs: {e}")


@app.task(name='toolkit.tasks.process_single_doc')
def process_single_doc(tokens, doc_id, user_id):
    creds = Credentials(
        client_id=config('GOOGLE_CLIENT_ID'),
        client_secret=config('GOOGLE_CLIENT_SECRET'),
        refresh_token=tokens['refresh_token'],
        token=tokens['access_token'],
        token_uri='https://oauth2.googleapis.com/token',
        scopes=['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive']
    )
    service = build('docs', 'v1', credentials=creds)
    doc = service.documents().get(documentId=doc_id).execute()
    html_content = document_to_html(doc)
    for obj_id, obj in doc.get('inlineObjects', {}).items():
        content_uri = obj['inlineObjectProperties']['embeddedObject']['imageProperties'].get('contentUri')
        if content_uri:
            response = requests.get(content_uri, headers={'Authorization': f'Bearer {creds.token}'})
            if response.status_ok:
                img = Image.open(BytesIO(response.content))
                img_path = f'images/{obj_id}.png'
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                img.save(img_path)
                upload_file_to_s3(f'toolkit/docs/{doc_id}/{img_path}', img_path)
                # Replace content URI with local path in HTML
                html_content = html_content.replace(content_uri,
                                                    f's3://||PLACEHOLDER||toolkit/docs/{doc_id}/{img_path}')
    mongo_client = MongoClient(config('MAC_MONGODB_CONNECTION_STRING'))
    db = mongo_client.your_database_name
    doc_uuid = str(uuid.uuid4())
    db.documents.insert_one({
        "content": html_content,
        "uuid": doc_uuid,
        "createdAt": datetime.now(),
        "sourceId": doc_id

    })
    client = chromadb.HttpClient(host=config('CHROMA_SERVER_HOST'), port=8000)
    # embeddings = OpenAIEmbeddings(
    #     model="text-embedding-3-small",
    #     openai_api_key=config("OPENAI_API_KEY"),
    #     openai_api_base=config('OPENAI_API_BASE'),
    #     headers={
    #         "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
    #     })
    #
    collection = client.get_or_create_collection("documents")
    #
    # text_splitter = SemanticChunker(embeddings)
    # docs = text_splitter.split_text(html_content)
    # metadatas = []
    # ids = []
    # chunks_to_save = []
    # for chunk in docs:
    #     chunk_id = str(uuid.uuid4())
    #     metadata = {
    #         "documentUUID": doc_uuid,
    #         "date": datetime.now(),
    #         "text": chunk,
    #         "userId": user_id,
    #         "sourceId": doc_id
    #     }
    #     metadatas.append(metadata)
    #     ids.append(chunk_id)
    #     chunks_to_save.append(chunk)
    # collection.add(documents=chunks_to_save, metadatas=metadatas, ids=ids)


def document_to_html(doc):
    content = doc.get('body').get('content')
    html = []
    for element in content:
        if 'paragraph' in element:
            paragraph = element.get('paragraph')
            html.append('<p>')
            for run in paragraph.get('elements'):
                if 'textRun' in run:
                    text_run = run.get('textRun')
                    text = text_run.get('content')
                    text_style = text_run.get('textStyle', {})
                    if text_style.get('link'):
                        url = text_style['link'].get('url', '#')
                        text = f'<a href="{url}">{text}</a>'
                    if text_style.get('bold'):
                        text = f'<strong>{text}</strong>'
                    if text_style.get('italic'):
                        text = f'<em>{text}</em>'
                    if text_style.get('underline'):
                        text = f'<u>{text}</u>'
                    html.append(text)
                elif 'inlineObjectElement' in run:
                    object_id = run['inlineObjectElement']['inlineObjectId']
                    inline_object = doc['inlineObjects'][object_id]
                    image_properties = inline_object['inlineObjectProperties']['embeddedObject']['imageProperties']
                    content_uri = image_properties.get('contentUri')
                    if content_uri:
                        html.append(f'<img src="{content_uri}" alt="Inline image" />')
            html.append('</p>')
        elif 'table' in element:
            html.append('<table border="1">')
            for row in element['table']['tableRows']:
                html.append('<tr>')
                for cell in row['tableCells']:
                    html.append('<td>')
                    for cell_content in cell['content']:
                        if 'paragraph' in cell_content:
                            for run in cell_content['paragraph']['elements']:
                                if 'textRun' in run:
                                    html.append(run['textRun']['content'])
                    html.append('</td>')
                html.append('</tr>')
            html.append('</table>')
    return ''.join(html)
