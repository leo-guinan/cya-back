from langchain.text_splitter import NLTKTextSplitter

from open_ai.api import OpenAIAPI
from transformer.transformers import podcast_transcript_to_summary, podcast_transcript_to_key_points, \
    podcast_transcript_to_links_to_include, summarize_podcast_section_summaries, summarize_podcast_section_key_points, \
    summarize_podcast_section_links_to_include, generate_show_notes


def transform_podcast_transcript(transcript):
    splitter = NLTKTextSplitter(chunk_size=8000, chunk_overlap=100)
    chunks = splitter.split_text(transcript)
    openai = OpenAIAPI()

    summary_chunks = []
    key_points_chunks = []
    links_to_include_chunks = []


    for chunk in chunks:
        summary_prompt = podcast_transcript_to_summary(chunk)
        key_points_prompt = podcast_transcript_to_key_points(chunk)
        links_to_include_prompt = podcast_transcript_to_links_to_include(chunk)
        summary = openai.complete(summary_prompt, stop_tokens=['The summary:'])
        key_points = openai.complete(key_points_prompt, stop_tokens=['The key points:'])
        links_to_include = openai.complete(links_to_include_prompt, stop_tokens=['The links to include:'])
        summary_chunks.append(summary)
        key_points_chunks.append(key_points)
        links_to_include_chunks.append(links_to_include)

    summary = openai.complete(summarize_podcast_section_summaries(summary_chunks) )
    key_points = openai.complete(summarize_podcast_section_key_points(key_points_chunks))
    links_to_include = openai.complete(summarize_podcast_section_links_to_include(links_to_include_chunks))
    show_notes = openai.complete(generate_show_notes(summary, key_points, links_to_include))

    return summary, key_points, links_to_include, show_notes

def create_embeddings_for_podcast_transcript(transcript):
    splitter = NLTKTextSplitter(chunk_size=15000, chunk_overlap=100)
    chunks = splitter.split_text(transcript)
    openai = OpenAIAPI()

    embeddings = []

    for chunk in chunks:
        embeddings.append(openai.embeddings(chunk))

    return embeddings
