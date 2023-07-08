from decouple import config
from notion_client import Client

class Notion():
    def __init__(self):
        self.notion = Client(auth=config('NOTION_API_KEY'))

    def add_chunks_to_page(self, page, chunks):
        for chunk in chunks:
            self.notion.blocks.children.append(page, children=[
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": chunk
                                }
                            }
                        ]
                    }
                }
            ])



    def client(self):
        return self.notion
