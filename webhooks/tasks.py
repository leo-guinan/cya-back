from backend.celery import app
from enhancer.service import enhance_twitter_account_with_summary
from mail.service import send_email
from open_ai.api import OpenAIAPI
from pinecone_api.pinecone_api import PineconeAPI
from search.models import ContentChunk, Content
from search.service import query_topics
from twitter.service import refresh_twitter_account_by_username




@app.task(name="process_twitter_user_for_experiment")
def twitter_user_experiment(twitter_username, for_author):
    twitter_account = refresh_twitter_account_by_username(twitter_username, client_account_id=1)
    enhanced_twitter_account = enhance_twitter_account_with_summary(twitter_account.twitter_id, 1)
    openai = OpenAIAPI()

    topic_embeddings = openai.embeddings(enhanced_twitter_account.summary, source="experiment")
    title, link, _description = query_topics(topic_embeddings, for_author)
    send_email(to="leo@definet.dev", message=f"Title: {title} Link: {link}", subject=f"Recommended podcast episode for {twitter_username}")
