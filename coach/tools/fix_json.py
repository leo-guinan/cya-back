from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI

from coach.tools.tool_class import ToolBase


class FixJSONTool(ToolBase):

    def __init__(self):
        fix_json_prompt_template = """
        There's an issue with this JSON.
        
        #JSON#
        {json}
        #END_JSON#
        
        Return the fixed JSON only. No prose.
        
        
        """
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")

        fix_json_prompt = PromptTemplate(
            template=fix_json_prompt_template,
            input_variables=["json"]

        )
        self.chain = LLMChain(
            llm=llm,
            verbose=True,
            prompt=fix_json_prompt,
        )

    def get_tool(self):
        return

    def fix_json(self, message):
        return self.chain.run(json=message)