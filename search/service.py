from langchain.text_splitter import NLTKTextSplitter

from open_ai.api import OpenAIAPI
import uuid

from pinecone.pinecone_api import PineconeAPI
from search.models import Content, ContentChunk


def save_item(text, title, description, link, content_type, creator):
    # get embeddings for text
    content = Content.objects.filter(link=link).first()

    if content is None:
        content = Content.objects.create(link=link, title=title, description=description, creator=creator, type=content_type)
        content.save()
        openai_api = OpenAIAPI()
        parent_id = uuid.uuid4()
        splitter = NLTKTextSplitter(chunk_size=15000, chunk_overlap=100)
        chunks = splitter.split_text(text)
        content_chunks = []

        for chunk in chunks:
            embeddings = openai_api.embeddings(chunk, source='search', parent_id=parent_id)
            content_chunk = ContentChunk.objects.create(content=content, text=chunk, embeddings=embeddings)
            content_chunk.save()
            content_chunks.append(content_chunk)

        pinecone = PineconeAPI()
        pinecone.upsert([(content_chunk.id, content_chunk.embeddings) for content_chunk in content_chunks])
        for content_chunk in content_chunks:
            content_chunk.embeddings_saved = True
            content_chunk.save()


    # return embeddings
