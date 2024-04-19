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

DELEGATION_PROMPT = """You are a powerful submind that is focused on {description}.

You have your own subminds that you can delegate tasks to.

Here are the subminds you currently have:
{subminds}

Here is your current goal: {goal}.

Here's what you currently know: {mind}

Based on what you know, what questions do you need to answer in order to accomplish your goal?

For each question, also identify which of your subminds should answer it. You can delegate each question to multiple 
subminds if appropriate.


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