from embeddings.vectorstore import Vectorstore


def save_document(document):
    vectorstore = Vectorstore()
    documents_to_save = []
    ids = []
    metadatas = []
    for section in document.sections.all():
        documents_to_save.append(section.text)
        ids.append(section.embedding_id)
        metadatas.append({
            "fulltext": document.id,
            "section": section.id,
            "link": document.url.id,
        })
    vectorstore.add_to_collection("searchables", documents_to_save, ids, metadatas)
    for section in document.sections.all():
        section.embeddings_saved = True
        section.save()
