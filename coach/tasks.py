import json
import os
import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from langchain import PromptTemplate, LLMChain
from langchain.agents import AgentType
from langchain.agents import initialize_agent
from langchain.agents import load_tools
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory
from langchain.tools import Tool, StructuredTool
from pydantic import Field, BaseModel

from backend.celery import app
from coach.models import User, InitialQuestion, UserAnswer, ChatSession, ChatError, ChatCredit, ChatPrompt, \
    ChatPromptParameter


class ToolInputSchema(BaseModel):
    client_info: str = Field()
    help_needed: str = Field()


@app.task(name="coach.tasks.respond_to_chat_message")
def respond_to_chat_message(message, user_id, session_id):
    channel_layer = get_channel_layer()
    user = User.objects.get(id=user_id)
    session = ChatSession.objects.filter(session_id=session_id).first()
    if session is None:
        session = ChatSession(user=user, session_id=session_id)
        session.save()
    try:

        # has user answered initial questions? If not, find first un-answered question and return that as response.
        message_history = MongoDBChatMessageHistory(
            connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
        )



        last_message = message_history.messages[-1] if message_history.messages else None

        print(last_message)
        questions = InitialQuestion.objects.all()
        if last_message is None:
            initial_question = questions.first()
            message_history.add_ai_message(initial_question.question)
            # need to send message to websocket
            async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": initial_question.question })
            return
            # return Response({'message': initial_question.question, 'session_id': session_id})
        for question in questions:
            if question.question == last_message.content:
                # save user answer
                user_answer = UserAnswer(answer=message, question=question, user=user)
                user_answer.save()
                message_history.add_user_message(message)
                # find next question
                next_question = InitialQuestion.objects.filter(index=question.index + 1).first()
                if next_question is None:
                    continue
                message_history.add_ai_message(next_question.question)
                # need to send message to websocket
                async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": next_question.question})
                return
                # return Response({'message': next_question.question, 'session_id': session_id})
        answers = UserAnswer.objects.filter(user=user).all()
        if answers is None:
            initial_question = InitialQuestion.objects.first()
            message_history.add_ai_message(initial_question.question)
            # need to send message to websocket
            async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": initial_question.question })
            return
            # return Response({'message': initial_question.question, 'session_id': session_id})
        memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history)

        # create prompt template partials
        partials = {}
        for answer in answers:
            partials[answer.question.prompt_variable] = answer.answer

        # System prompt for chatbot
        system_prompt_template = """
            You are a database system for a professional coach.
    
            Your job is to help the coach by providing them with information about the client.
    
            Here's the information you have about your client.
    
            Here's what your client is building:
            {client_project}
    
            Here is their biggest strengths:
            {client_strengths}
    
            Here is their biggest challenges:
            {client_challenges}
    
            Here is the format they prefer to create content in:
            {client_format}
    
            Here is their story:
            {client_story}
    
            Here is their progress:
            {client_progress}
    
            Here is their Big Hairy Audacious Goal:
            {client_goal}
    
            Here's their current small goal:
            {client_small_goal}
    
            Here's what they are trying to achieve:
            {client_achieve}
            """

        system_prompt = PromptTemplate(
            template=system_prompt_template,
            partial_variables=partials,
            input_variables=[
                "client_achieve"
            ]
        )
        llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")
        conversation = LLMChain(
            llm=llm,
            verbose=True,
            memory=memory,
            prompt=system_prompt,
        )
        background_tool = Tool.from_function(
            func=conversation.run,
            name="ClientBackground",
            description="useful for when you need to get information about the client or what they are working on"
            # coroutine= ... <- you can specify an async method if desired as well
        )

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

        coach = LLMChain(
            llm=llm,
            memory=memory,
            verbose=True,
            prompt=coach_prompt,
        )

        coach_tool = Tool.from_function(
            func=coach.run,
            name="Coach",

            description="useful for when you need to provide coaching to the client",
            # coroutine= ... <- you can specify an async method if desired as well
        )

        whats_needed_prompt_template = """
            You are a research assistant helping a professional coach with their client.
    
            Your job is to figure out if you have enough information for the coach to assist the client.
    
            If you need more information, specify what information you need.
    
            If you don't need more information, say that you have enough information to answer confidently.
    
            Here's what you are trying to help the client with: {help_needed}
    
            Here's the information you have about the client: {client_info}
    
            What information do you need to make the most helpful recommendation possible?
            """

        whats_needed_prompt = PromptTemplate(
            template=whats_needed_prompt_template,
            input_variables=["help_needed", "client_info"]
        )

        whats_needed = LLMChain(
            llm=llm,
            verbose=True,
            prompt=whats_needed_prompt,
        )

        whats_needed_tool = StructuredTool.from_function(
            func=whats_needed.run,
            name="WhatsNeeded",
            description="useful for when you need to figure out if you have enough information from the client",
            args_schema=ToolInputSchema,

            # coroutine= ... <- you can specify an async method if desired as well
        )

        tools = [background_tool, coach_tool, whats_needed_tool]
        agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

        response = agent.run(message)


        alix_template = ChatPrompt.objects.get(name="COACH")
        alix_params = ChatPromptParameter.objects.filter(prompt=alix_template).all()

        alix_prompt = PromptTemplate(
            template=alix_template.prompt,
            input_variables=[param.name for param in alix_params]
        )
        alix = LLMChain(
            llm=llm,
            verbose=True,
            prompt=alix_prompt,

        )

        alix_response = alix.run(
            question=message,
            response=response
        )

        # record chat credit used
        chat_credit = ChatCredit(user=user, session=session)
        chat_credit.save()

        # need to send message to websocket
        async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": alix_response})
    except Exception as e:
        error = str(e)
        print(error)
        chat_error = ChatError(error=error, session=session)
        chat_error.save()
        async_to_sync(channel_layer.group_send)(session_id, {"type": "chat.message", "message": "Sorry, there was an error processing your request. Please try again."})




@app.task(name="chatbot.tasks.save_client_info")
def save_client_info(session_id, message):

    pass