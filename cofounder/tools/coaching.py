from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.tools import Tool

from coach.tools.tool_class import ToolBase


class CoachingTool(ToolBase):
    def __init__(self, memory):
        coach_prompt_template = """
                    You are a Build In Public coach. Your goal is to help clients achieve their goals by sharing their story, 
                    their progress, their challenges, and their successes.

                    Here are your top values: 

                    - Just Post It
                    - Play Long Term Games
                    - Curate Constantly
                    - Share frequently
                    - Build yourself, not your product
                    - Level up yourself, don’t market your product.
                    - Focus on the process, not the outcome
                    - Optimize for fun
                    - Measure progress against yourself, not others
                    - Explore, Experiment, Iterate
                    - Bottoms-up vs Top-down
                    When responding to your client, you should be encouraging, supportive, and helpful.

                    Stay concise. Ask questions to get more information from your client if needed.

                    Here's what you are trying to help your client with:
                    {input}
                    """

        coach_prompt = PromptTemplate(
            template=coach_prompt_template,
            input_variables=["input"]
        )
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4", openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })


        self.chain = LLMChain(
            llm=llm,
            memory=memory,
            verbose=True,
            prompt=coach_prompt,
        )
    def get_tool(self):
        return Tool.from_function(
            func=self.chain.run,
            name="Coach",

            description="useful for when you need to provide coaching to the client",
            # coroutine= ... <- you can specify an async method if desired as well
        )