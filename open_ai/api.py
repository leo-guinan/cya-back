import uuid

import openai
from decouple import config

from open_ai.models import OpenAICall


class OpenAIAPI:
    def __init__(self):
        openai.api_key = config('OPENAI_API_KEY')

    def complete(self,
                 prompt,
                 source,
                 parent_id = None,
                 stop_tokens=None,
                 max_tokens=1024,
                 temperature=0.7,
                 top_p=1,
                 frequency_penalty=0,
                 presence_penalty=0,
                 engine='text-davinci-003'
                 ):
        if stop_tokens:
            response = openai.Completion.create(model=engine,
                                                prompt=prompt,
                                                temperature=temperature,
                                                max_tokens=max_tokens,
                                                stop=stop_tokens
                                                )
        else:
            response = openai.Completion.create(model=engine,
                                                prompt=prompt,
                                                temperature=temperature,
                                                max_tokens=max_tokens,
                                                )
        call = OpenAICall(tokens_used=response['usage']['total_tokens'],
                          source=source,
                          request_id=uuid.uuid4(),
                          request_type='completion',
                          model=engine,
                          parent_id=parent_id
                          )
        call.save()
        return response.choices[0].text

    def embeddings(self,
                   text,
                   source,
                 parent_id = None,
                   ):
        response = openai.Embedding.create(input=text, engine='text-embedding-ada-002')
        call = OpenAICall(tokens_used=response['usage']['total_tokens'],
                          source=source,
                          request_id=uuid.uuid4(),
                          request_type='embedding',
                          model='text-embedding-ada-002',
                          parent_id=parent_id
                          )
        call.save()
        return response['data'][0]['embedding']
