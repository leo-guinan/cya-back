import re

import feedparser


def parse_feed(url):
    feed = feedparser.parse(url)
    return feed

def get_link_for_entry(entry):
    for link in entry.links:
        if link['type'] == 'audio/mpeg':
            title = "".join([c for c in entry['title'] if re.match(r"\w", c)])
            url = link['href']
            return title,url
    return None