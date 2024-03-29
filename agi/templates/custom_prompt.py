from typing import Callable, List

from langchain_core.messages import HumanMessage, BaseMessage
from langchain_core.prompts import StringPromptTemplate, ChatPromptTemplate, BaseChatPromptTemplate
from langchain_core.tools import Tool


# Set up a prompt template
class CustomPromptTemplate(BaseChatPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    conversation_history: List[BaseMessage]

    def format_messages(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])

        kwargs["conversation_history"] = "\n".join([f"{message.role}:{message.content}" for message in self.conversation_history])

        print(kwargs)
        formatted = self.template.format(**kwargs)
        return [HumanMessage(content=formatted)]

