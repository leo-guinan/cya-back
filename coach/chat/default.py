import json

from asgiref.sync import async_to_sync
from decouple import config
from langchain import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import MongoDBChatMessageHistory, ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder, HumanMessagePromptTemplate
from langchain.schema import SystemMessage

from coach.models import ChatCredit, ChatError
from coach.tools.background import BackgroundTool
from coach.tools.chat_namer import ChatNamerTool
from coach.tools.coaching import CoachingTool
from coach.tools.fix_json import FixJSONTool
from coach.tools.lookup import LookupTool
from coach.tools.needed import WhatsNeededTool


def run_default_chat(session, message, user, channel_layer):
    fix_json_tool = FixJSONTool()


    try:
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": "Looking up chat history...",
                                                 "id": -1})

        # has user answered initial questions? If not, find first un-answered question and return that as response.
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session.session_id
        )

        memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history)

        # System prompt for chatbot
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4",
                         openai_api_base=config('OPENAI_API_BASE'), headers={
                "Helicone-Auth": f"Bearer {config('HELICONE_API_KEY')}"
            })

        coach_tool = CoachingTool(memory=memory)
        whats_needed_tool = WhatsNeededTool()
        background_tool = BackgroundTool()

        # determine what's needed to answer the query
        raw_ans = whats_needed_tool.process_question(message)
        print(raw_ans)
        try:
            questions = json.loads(raw_ans)['questions']
        except Exception as e:
            # if json fails, try to fix it with gpt 4
            raw_ans = fix_json_tool.fix_json(raw_ans)
            questions = json.loads(raw_ans)['questions']
        answers = []
        for question in questions:
            answers.append({

                "question": question['question'],
                "answer": background_tool.answer_question(question, user.id)

            })

        print(answers)

        # if not, ask clarifying questions

        # see if any sources can provide extra support to answer the question

        # create a response

        # tools = [coach_tool.get_tool(), whats_needed_tool.get_tool()]
        # agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)
        #
        # response = agent.run(message)
        #
        # # You are Alix, the Build In Public Coach.
        # #
        # #
        # #
        # #
        # #  {human_input}.
        # #
        # # Here is the feedback from your team: {response}
        # #
        # # Your job is to take their response and convert it to a useful response for your client in your voice.
        # #
        # # You are in a real time chat, so keep your responses short and feel free to ask small, clarifying questions.  You don't want to overwhelm the client with
        # #
        # #
        # #
        # #
        # # your response
        #
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": "Doing research...", "id": -1})

        response = "\n".join([f"Question: {answer['question']}: {answer['answer']}" for answer in answers])
        lookup_tool = LookupTool()
        document = lookup_tool.lookup(message)
        print(document)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=f"""
                You are Alix, the Build In Public Coach. You are friendly, informal, and tech-savvy.

                You believe that building in public is a great way to empower people to build their own businesses.

                You are supportive, encouraging, and helpful.

                Your team has researched the following question from your client: {message}
                They've looked up the information they have on your client and came up with the following questions and answers
                from their database.
                {response}

                You looked up the question in your research library and found the following answer:
                {document['result']}


                Your job is to take their response and convert it to a useful response for your client in your voice.
                If you need more information, feel free to ask small, clarifying questions.  You don't want to overwhelm the client with
                too large a response.
                """),
            # The persistent system prompt
            MessagesPlaceholder(variable_name="chat_history"),  # Where the memory will be stored.
            HumanMessagePromptTemplate.from_template("{human_input}"),  # Where the human input will injectd
        ])

        print(prompt)
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": "Thinking...", "id": -1})

        alix_memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True,
                                               chat_memory=message_history)

        chat_llm_chain = LLMChain(
            llm=llm,
            prompt=prompt,
            verbose=True,
            memory=alix_memory,
        )

        # alix_memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history, input_key="human_input")

        alix_response = chat_llm_chain.predict(
            human_input=message,
        )

        # record chat credit used
        chat_credit = ChatCredit(user=user, session=session)
        chat_credit.save()
        # print(alix_response)

        source_markdown = "\n\n".join(
            [f"""[{source.metadata['title']}]({source.metadata['url']})""" for source in document['source_documents']])

        composite_response = f"""
    {alix_response}

    Sources:

    {source_markdown}
            """

        print(composite_response)
        # need to send message to websocket
        async_to_sync(channel_layer.group_send)(session.session_id,
                                                {"type": "chat.message", "message": composite_response, "id": -1})
    except Exception as e:
        error = str(e)
        print(f'Error: {e}')
        chat_error = ChatError(error=error, session=session)
        chat_error.save()
        async_to_sync(channel_layer.group_send)(session.session_id, {"type": "chat.message",
                                                             "message": "Sorry, there was an error processing your request. Please try again.", "id": -1})
