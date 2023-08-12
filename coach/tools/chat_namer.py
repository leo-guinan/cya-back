from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

from coach.tools.tool_class import ToolBase


class ChatNamerTool(ToolBase):

        def __init__(self):
            name_chat_prompt_template = """
                  This message is the start of a new chat session. Name the chat session based on the topic.
                  
                  Message:
                  {message}
                  
                  return the name in the following JSON format:
                  {{
                    "name": "<name>"
                    }}


                   """
            llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'))

            name_chat_prompt = PromptTemplate(
                template=name_chat_prompt_template,
                input_variables=["message"]

            )
            self.chain = LLMChain(
                llm=llm,
                verbose=True,
                prompt=name_chat_prompt,
            )


        def name_chat(self, message):
            return self.chain.run(message=message)

        def get_tool(self):
            pass