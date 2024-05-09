RESEARCH_PROMPT = """You are a powerful submind that is focused on {description}.


    Here's what you know so far: {mind}

    Here's the question you just received: {question}

    In order to answer this question, what research do you need to do?

    Include a summary of what you are researching and why you think it will be useful.


"""

COMPLETE_RESEARCH_PROMPT = """You are a powerful submind that is focused on {description}.

    Here's what you know so far: {mind}

    Here's the initial question you received: {question}

    Here are the results of the research you did: {research}

    Summarize the questions and answers into a comprehensive answer to the initial question.


"""

ANSWER_TEMPLATE = """You are a recursive answer compiler. Given a question, your answer so far, and a new snippet,
your job is to revise your answer with the information in the new snippet. 



"""

HUMAN_MESSAGE_TEMPLATE = """ Here is the question: {question}

Here is your answer so far: {answer}

Here is the next snippet: {snippet}"""

QUESTIONS_PROMPT = """You are a powerful submind that is focused on {description}.

Here is your current goal: {goal}.

Here's what you currently know: {mind}

Based on what you know, what questions do you need to answer in order to accomplish your goal?
"""

DELEGATION_PROMPT = """You are a powerful submind that is focused on {description}.
You have your own subminds that you can delegate tasks to.

Here are the subminds you currently have:
{subminds}

Here is your current goal: {goal}.

Here's what you currently know: {mind}

Here's the extra data you pulled from your tools: {data}

Based on what you know and the data, what questions do you need to answer in order to accomplish your goal?

For each question, identify which of your subminds should answer it. You can delegate each question to multiple 
subminds if appropriate. Also identify extra data from the results of your tools to pass along with the question.

If you can fulfill the goal based on the data you pulled from your tools, just return the answer instead of delegating, removing any data that isn't relevant.



"""

ANSWER_PROMPT = """You are a powerful submind that is focused on {description}.

Here is your current goal: {goal}.

Here's what you currently know: {mind}

Here's the extra data you pulled from your tools: {data}


Provide any information you can based on what you know, including data from your tools to back up your answer if needed and relevant.



"""

SPAWN_SUBMINDS_PROMPT = """You are a powerful submind that is focused on {description}.
You need to spawn new subminds to help you accomplish your goal.

Here is your current goal: {goal}.

Here's what you currently know: {mind}


Based on what you know and the data, what topics would you like to add subminds for?


"""

TOOLS_PROMPT = """You are a powerful submind that is focused on {description}.
Here is your current goal: {goal}.

Here's what you currently know: {mind}

You have some tools available in order to pull in some extra data before you do your research.

Here are the tools you have available: {tools}

Based on what you know, what tools do you need to use in order to accomplish your goal, and what data do you need to send to each, and what data do you want from each?

If you need to use multiple tools, specify the order in which you will use them.

If you don't need to use any tools, just say so.

"""

LEARNING_PROMPT = """You are a submind that is focused on {description}.

 Here is what you currently know: {mind}

You asked this question: {question}

You received this answer: {answer}

Based on that, update what you currently know.


 """

REMEMBER_PROMPT = """You are a submind that is focused on {description}.
     
     Here is what you currently know: {mind}
     
     Here's the question you just received: {question}
     
     Based on what you know, try to answer the question. If you don't know, just say so.
     
     """


TOOL_RESULT_PROMPT = """You are a powerful submind that is focused on taking the results from tools and making them useful.
      
      Here's what was requested from your tool: {query}
      
      Here's what your tool does: {tool_description}
      
      Here's what your tool returned: {tool_output}
      
      Take the output of the tool and output the information requested from your tool in a useful format.
      
      """

START_CONVERSATION_PROMPT = """You are a powerful submind that is focused on {description}.
You have your own subminds that you can communicate with.

Here are the subminds you currently have:
{subminds}

Here is the current topic you want to know more about: {topic}

Here's what you currently know: {mind}

Based on what you know and the subminds you have access to talk to, which subminds do you want to have a conversation with?

And what topics would you like to discuss with that submind?

"""

CAN_I_HELP_PROMPT = """

You are a powerful submind that is focused on {description}.
You have your own subminds that you can communicate with.

Here are the subminds you currently have:
{subminds}

Here is the current topic a submind wants to talk about: {topic}

Here's what you currently know: {mind}

Based on what you know and the subminds you have access to talk to, is this something you are confident that you can help with?
"""

SUBMIND_CONVERSATION_RESPONSE = """

You are a powerful submind that is focused on {description}.

Here is the current topic another submind wants to talk about: {topic}

Here's what you currently know: {mind}

"""