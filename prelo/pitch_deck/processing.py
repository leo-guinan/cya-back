import base64
import os
import tempfile
import time
import uuid

import fitz
from decouple import config
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

from prelo.aws.s3_utils import upload_file_to_s3, download_file_from_s3
from prelo.models import PitchDeck, PitchDeckAnalysis, PitchDeckSlide
from prelo.prompts.prompts import PITCH_DECK_SLIDE_PROMPT


def prep_deck_for_analysis(pitch_deck: PitchDeck):
    try:
        start_time = time.perf_counter()
        temp_file = download_file_from_s3(pitch_deck.s3_path)

        image_dir = tempfile.gettempdir()
        imgs = pdf_to_images(temp_file, image_dir)

        raw_slides = []
        for img in imgs:
            image_uri = img['path']

            print(f"Analyzing image: {image_uri}")
            base64_image = encode_image(image_uri)
            model = ChatOpenAI(model="gpt-4-turbo", openai_api_key=config("OPENAI_API_KEY"))
            message = HumanMessage([
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}",
                        "detail": "auto"
                    }
                },
                {
                    "type": "text",
                    "text": PITCH_DECK_SLIDE_PROMPT
                }
            ])
            response = model.invoke([message])
            img_key = f"{pitch_deck.id}/{image_uri.split('/')[-1]}"
            upload_file_to_s3(img_key, image_uri)
            PitchDeckSlide.objects.create(
                deck=pitch_deck,
                s3_path=img_key,
                order=img['page'],
                content=response.content,
                uuid=str(uuid.uuid4())
            )

            raw_slides.append({
                'path': image_uri,
                'response': response.content
            })
            cleanup_local_file(image_uri)
        cleanup_local_file(temp_file)
        # print("All slides analyzed, cleaning data")
        # cleaned_data = clean_data(raw_slides)
        combined = "\n".join([f"Page: {slide['path']}\n{slide['response']}" for slide in raw_slides])
        print("Data ingested. Starting analysis")
        analysis = PitchDeckAnalysis.objects.create(
            deck=pitch_deck,
            compiled_slides=combined
        )
        pitch_deck.status = PitchDeck.READY_FOR_ANALYSIS
        pitch_deck.save()
        end_time = time.perf_counter()
        analysis.processing_time = end_time - start_time
        analysis.save()
        return analysis


    except Exception as e:
        print(f"Error processing pitch deck: {e}")
        pitch_deck.status = PitchDeck.ERROR
        pitch_deck.error= str(e)
        pitch_deck.save()
        raise e


def pdf_to_images(pdf_path, output_folder):
    imgs = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # number of page
        pix = page.get_pixmap()
        output_path = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_path)
        imgs.append({
            "path": output_path,
            "page": page_num + 1
        })
    return imgs


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def cleanup_local_file(path):
    """
    Delete a file from the local filesystem.

    :param path: str, the path to the file to be deleted
    """
    if os.path.exists(path):
        os.remove(path)
