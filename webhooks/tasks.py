from backend.celery import app
from enhancer.service import enhance_twitter_account_with_summary
from mail.service import send_email
from open_ai.api import OpenAIAPI
from pinecone_api.pinecone_api import PineconeAPI
from search.models import ContentChunk, Content
from twitter.service import refresh_twitter_account_by_username



def query_topics(topics, for_author):
    pinecone = PineconeAPI()
    results = pinecone.search(query_vector=topics, k=10, metadata={"author": {"$eq": for_author}} if for_author else None)
    matched_chunks= []
    for result in results.matches:
        chunk = ContentChunk.objects.filter(chunk_id=result.id).first()
        matched_chunks.append(chunk)
    matched_content_ids = [chunk.content_id for chunk in matched_chunks]
    id_of_max_count_matched = max(matched_content_ids, key=matched_content_ids.count)
    matched_content = Content.objects.filter(id=id_of_max_count_matched).first()
    return matched_content.title, matched_content.link
@app.task(name="process_twitter_user_for_experiment")
def twitter_user_experiment(twitter_username, for_author):
    twitter_account = refresh_twitter_account_by_username(twitter_username, client_account_id=1)
    enhanced_twitter_account = enhance_twitter_account_with_summary(twitter_account.twitter_id, 1)
    openai = OpenAIAPI()

    topic_embeddings = openai.embeddings(enhanced_twitter_account.summary, source="experiment")
    title, link = query_topics(topic_embeddings, for_author)
    send_email(to="leo@definet.dev", message=f"Title: {title} Link: {link}", subject=f"Recommended podcast episode for {twitter_username}")
