import logging

from embeddings.vectorstore import Vectorstore
logger = logging.getLogger(__name__)

def save_document(document, collection="searchables"):
    logger.info("saving document")
    vectorstore = Vectorstore()
    documents_to_save = []
    ids = []
    metadatas = []
    for section in document.sections.all():
        if section.embeddings_saved or len(section.text) == 0:
            continue
        documents_to_save.append(section.text)
        ids.append(section.embedding_id)
        metadatas.append({
            "fulltext": document.id,
            "section": section.id,
            "link": document.url.id,
        })
    vectorstore.add_to_collection(collection, documents_to_save, ids, metadatas)
    for section in document.sections.all():
        section.embeddings_saved = True
        section.save()
