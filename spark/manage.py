import logging
import os
import uuid
from datetime import datetime

import requests

from content.audio import transcribe_audio
from content.rss import parse_feed, get_link_for_entry
from search.models import Link, Fulltext, Section

logger = logging.getLogger(__name__)

def add_rss_feed(url, title):
    # see if url already exists
    logger.info("adding rss feed")
    link = Link.objects.filter(url=url).first()
    if not link:
        link = Link()
        link.url = url
        link.title = title
        link.save()
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

    for child_link in link.children.all():
        logger.info("processing podcast episode")
        process_podcast(child_link)

    link.processed = True
    link.save()
    return link

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
        logger.info("transcribing audio")
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
        link.save()
    except Exception as e:
        logger.error(e)
    finally:
        os.remove(file_name)

