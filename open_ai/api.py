from decouple import config

import openai


class OpenAIAPI:
    def __init__(self):
        openai.api_key = config('OPENAI_API_KEY')

    def complete(self,
                 prompt,
                 stop_tokens = None,
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
        return response.choices[0].text

    def embeddings(self, text):
        return openai.Embedding.create(input=text, engine='text-embedding-ada-002')['data'][0]['embedding']
