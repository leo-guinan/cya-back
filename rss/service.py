import feedparser

# a function that takes an rss feed url and returns a list of dictionaries
# containing the feed's title, link, and summary
def parse_feed(url):
    feed = feedparser.parse(url)
    entries = []
    for entry in feed.entries:
        entries.append({
            'title': entry.title,
            'links': entry.links,
            'summary': entry.summary,
        })
    return entries


# a function that takes a list of dictionaries and prints them nicely
def print_entries(entries):
    for entry in entries:
        print(entry['title'])
        print(entry['links'])
        print(entry['summary'])
        print()

# a function that takes a list of dictionaries and extracts all links from the summary
def extract_links(entries):
    links = []
    for entry in entries:
        links.append(entry.summary.find(r'href="(.+?)"'))
    return links