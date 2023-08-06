from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.tools import StructuredTool
from pydantic import BaseModel, Field

from coach.tools.tool_class import ToolBase


class ToolInputSchema(BaseModel):
    client_info: str = Field()
    help_needed: str = Field()


class WhatsNeededTool(ToolBase):

    def __init__(self):
        whats_needed_prompt_template = """
                    You are a research assistant helping a professional coach with their client.

                    Your job is to figure out if you have enough information for the coach to assist the client.

                    If you need more information, specify what information you need.

                    If you don't need more information, say that you have enough information to answer confidently.

                    Here's what you are trying to help the client with: {help_needed}

                    What questions do you have for the client?
                    
                    Respond in the following JSON format: 
                    {{
                    "questions": [
                    {{
                    "question": "<question>"
                    }},
                    ...
                    ]
                    }}
                    """

        whats_needed_prompt = PromptTemplate(
            template=whats_needed_prompt_template,
            input_variables=["help_needed"]
        )
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")

        self.chain = LLMChain(
            llm=llm,
            verbose=True,
            prompt=whats_needed_prompt,
        )

    def get_tool(self):
        return StructuredTool.from_function(
            func=self.chain.run,
            name="WhatsNeeded",
            description="useful for when you need to figure out if you have enough information from the client",
            args_schema=ToolInputSchema,

            # coroutine= ... <- you can specify an async method if desired as well
        )

    def process_question(self, question):
        return self.chain.run(help_needed=question)
