LEARN_FROM_TEXT_PROMPT = """You are a powerful submind that is learning from what you read.

Here is your current knowledge base: {knowledge_base}

Here is what you are trying to learn more about: {what_to_learn}

Here is the new input you've read: {text}

Based on this, what new information does this text provide? If no new relevant information, just return ""

"""

INTEGRATE_LEARNING_PROMPT = """ You are a powerful submind that is integrating new information into your knowledge base.

Here is your current knowledge base: {knowledge_base}

Here is the new information you are trying to integrate: {new_information}

Based on this, rewrite your knowledge base to include this new information.

"""

COMPRESS_INVESTOR_KNOWLEDGE_PROMPT = """You are a powerful submind that is compressing your knowledge about an investor.

Here is your current knowledge base: {knowledge_base}

It contains a lot of raw data based on processes you've run. Now that you are done, create a compact report of
the investment firm's thesis and the investor's personal values, investment thesis, and what they are looking for
 when investing in companies.
 """

COMPRESS_KNOWLEDGE_PROMPT = """You are a powerful submind that is compressing your knowledge about {topic}.


Here is your current knowledge base: {knowledge_base}

It contains a lot of raw data based on processes you've run. Now that you are done, create a compact report of
the information you've learned.
"""