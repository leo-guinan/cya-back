import requests
from decouple import config

from podcast.podscan import look_for_podcast_episodes
from submind.memory.memory import remember
from submind.models import Submind
from toolkit.tools.web_scraper import crawl, scrape


def google_search(query, api_key, cse_id, num_results=5):
    url = f"https://www.googleapis.com/customsearch/v1"
    params = {
        'key': api_key,
        'cx': cse_id,
        'q': query,
        'num': num_results,
    }
    response = requests.get(url, params=params)
    return response.json()

def podcast_search(person_name: str, submind: Submind):
    episodes = look_for_podcast_episodes(person_name)




def find_links_about_person(person_name: str, namespace: str, submind: Submind):
    # Placeholder function
    # Add your scraping code here
    # Replace these with your actual API key and CSE ID
    api_key = config('CUSTOM_SEARCH_API_KEY')
    cse_id = config('CUSTOM_SEARCH_ENGINE_ID')

    # Investor's name

    # Search queries based on the instructions
    queries = [
        f'{person_name} investor',
        f'{person_name} podcast',
        f'{person_name} blog',
        f'{person_name} interview',
        f'{person_name} news',
    ]
    session = requests.Session()
    session.verify = False
    for query in queries:
        print(f"Searching for: {query}")
        results = google_search(query, api_key, cse_id)
        if 'items' in results:
            for item in results['items']:
                print("Crawling...")
                scrape(item['link'], session, namespace, submind)
                print(f"Title: {item['title']}")
                print(f"Link: {item['link']}")
                print(f"Snippet: {item['snippet']}")
                print()
        else:
            print("No results found.")
        print("=" * 40)


def learn_about_person(person_name: str, namespace: str, submind_id: int):
    submind = Submind.objects.get(id=submind_id)
    find_links_about_person(person_name, namespace, submind)
    # podcast_search(person_name, submind)

