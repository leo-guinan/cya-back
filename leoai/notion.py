from decouple import config
from notion_client import Client

class Notion():
    def __init__(self):
        self.notion = Client(auth=config('NOTION_API_KEY'))

    def add_chunks_to_page_property(self, page, chunks):
        children = []
        for chunk in chunks:
            children.append({
                "type": "text",
                "text": {
                    "content": chunk,
                    "link": None
                },
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": False,
                    "color": "default"
                },
                "plain_text": chunk,
                "href": None
            })

        self.notion.pages.update(page, properties={'Transcript': children})



    def client(self):
        return self.notion
