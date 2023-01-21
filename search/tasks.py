from backend.celery import app
from search.models import Content, ContentChunk
from search.service import split, save_embeddings, get_embeddings


@app.task(name="search.save_content")
def save_content_task(content_id):
    content = Content.objects.filter(id=content_id).first()
    if not content:
        return

    chunk_ids = split(content)
    for chunk_id in chunk_ids:
        get_embeddings_for_chunk.delay(chunk_id, content.creator.email, content.type)


@app.task(name="search.save_content_chunk")
def save_chunk(content_chunk_id, email, content_type):
    save_embeddings(content_chunk_id, email, content_type)

@app.task(name="search.get_embeddings_for_chunk")
def get_embeddings_for_chunk(content_chunk_id, email, content_type):
    chunk_id = get_embeddings(content_chunk_id)
    save_chunk.delay(chunk_id, email, content_type)


@app.task(name="search.save_unsaved_chunks")
def save_unsaved_chunks():
    content_chunks = ContentChunk.objects.filter(embeddings_saved=False).all()
    for content_chunk in content_chunks:
        save_chunk.delay(content_chunk.id, content_chunk.content.creator.email, content_chunk.content.type)
