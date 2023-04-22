import logging
import os
import uuid
from datetime import datetime

import requests

from content.audio import transcribe_audio
from content.rss import parse_feed, get_link_for_entry
from embeddings.vectorstore import Vectorstore
from search.models import Link, Recommendation, Fulltext, Section, SearchEngine, SearchableLink

logger = logging.getLogger(__name__)


def add_recommended_link(url, title, user, recommendation_text, affiliate_link):
    # see if url already exists
    link = Link.objects.filter(url=url).first()
    if not link:
        link = Link()
        link.url = url
        link.title = title
        link.save()
    # add recommendation
    recommendation = Recommendation()
    recommendation.url = link
    recommendation.text = recommendation_text
    recommendation.author = user
    recommendation.affiliate_link = affiliate_link
    recommendation.save()


def add_searchable_link(search_engine, title, url, description, image):
    link = Link.objects.filter(url=url).first()
    if not link:
        link = Link()
        link.url = url
        link.title = title
        link.save()
    engine = SearchEngine.objects.filter(slug=search_engine).first()
    vectorstore = Vectorstore()
    if not engine:
        engine = SearchEngine()
        engine.slug = search_engine
        vectorstore.create_collection(search_engine)
        engine.save()
    searchable_link = SearchableLink.objects.filter(url=link, search_engine=engine).first()
    if not searchable_link:
        searchable_link = SearchableLink()
        searchable_link.url = link
        searchable_link.search_engine = engine
        searchable_link.description = description
        searchable_link.image = image
        searchable_link.uuid = uuid.uuid4()
        searchable_link.title = title
        searchable_link.save()

        vectorstore.add_to_collection(search_engine, [f"{title}\n{description}"], [str(searchable_link.uuid)],
                                      [{"link": link.id, "searchable_link": searchable_link.id}])



def process_youtube(url):
    # download video
    # extract audio
    # transcribe
    # add to db
    pass


def process_podcast(link):
    logger.info("processing podcast")

    if link.processed:
        return
    url = link.url
    fulltext = Fulltext()
    fulltext.url = link
    fulltext.save()
    file_name = url.split("/")[-1]
    file_name = file_name.split("?")[0]
    try:
        r = requests.get(url)
        with open(file_name, "wb") as f:
            f.write(r.content)
        chunks = transcribe_audio(file_name)
        if len(chunks) == 0:
            return
        fulltext.text = "\n".join(chunks)
        fulltext.save()
        for chunk in chunks:
            section = Section()
            section.fulltext = fulltext
            section.text = chunk
            embedding_id = uuid.uuid4()
            section.embedding_id = embedding_id
            section.save()
        link.processed = True
        link.processed_at = datetime.now()
        link.save()
    except Exception as e:
        logger.error(e)
    finally:
        os.remove(file_name)


def process_article(url):
    pass


def process_rss_feed(link):
    logger.info("processing rss feed")
    if link.processed:
        return
    parsed_feed = parse_feed(link.url)
    entries = parsed_feed.entries
    for entry in entries:
        title, child = get_link_for_entry(entry)
        if (child):
            child_link = Link()
            child_link.url = child
            child_link.title = title
            child_link.save()
            link.children.add(child_link)
            process_link(child_link)

    link.processed = True
    link.processed_at = datetime.now()
    link.save()


def process_link(link):
    type = get_content_type(link)
    if type == "youtube":
        process_youtube(link)
    elif type == "podcast":
        process_podcast(link)
    elif type == "rss":
        process_rss_feed(link)
    else:
        process_article(link)


def is_youtube(url):
    return "youtube" in url


def is_podcast(url):
    return '.mp3' in url


def is_rss_feed(url):
    return '.xml' in url or '.rss' in url


def get_content_type(link):
    if is_youtube(link.url):
        return "youtube"
    elif is_podcast(link.url):
        return "podcast"
    elif is_rss_feed(link.url):
        return "rss"
    else:
        return "article"
