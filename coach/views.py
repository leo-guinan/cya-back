import json
import uuid

from decouple import config
from langchain import OpenAI, ConversationChain, PromptTemplate, LLMChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory, MongoDBChatMessageHistory

from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework_api_key.permissions import HasAPIKey

from coach.models import InitialQuestion, UserAnswer, User


# Create your views here.

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def chat(request):
    body = json.loads(request.body)
    message = body['message']
    user_id = body['user_id']
    session_id = body.get('session_id', str(uuid.uuid4()))
    user = User.objects.get(id=user_id)
    # has user answered initial questions? If not, find first un-answered question and return that as response.
    message_history = MongoDBChatMessageHistory(
        connection_string=config('MONGODB_CONNECTION_STRING'), session_id=session_id
    )

    if session_id == user.initial_session_id:

        last_message = message_history.messages[-1] if message_history.messages else {"content": ""}

        questions = InitialQuestion.objects.all()
        for question in questions:
            if question.question == last_message.content:
                # save user answer
                user_answer = UserAnswer(answer=message, question=question, user=user)
                user_answer.save()
                message_history.add_user_message(message)
                # find next question
                next_question = InitialQuestion.objects.filter(index=question.index+1).first()
                if next_question is None:
                    continue
                message_history.add_ai_message(next_question.question)
                return Response({'message': next_question.question, 'session_id': session_id})
    answers = UserAnswer.objects.filter(user=user).all()
    if answers is None:
        initial_question = InitialQuestion.objects.first()
        message_history.add_ai_message(initial_question.question)
        return Response({'message': initial_question.question, 'session_id': session_id})
    memory = ConversationBufferMemory(memory_key="history", chat_memory=message_history)

    # create prompt template partials
    partials = {}
    for answer in answers:
        partials[answer.question.prompt_variable] = answer.answer

    # System prompt for chatbot
    system_prompt_template = """
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

    Here is the history of your conversations:
    {history}

    Here's their next message:
    {input}
    """

    system_prompt = PromptTemplate(
        template=system_prompt_template,
        partial_variables=partials,
        input_variables=[
            "history",
            "input"
        ]
    )
    llm = ChatOpenAI(temperature=0, openai_api_key=config('OPENAI_API_KEY'), model_name="gpt-4")
    conversation = LLMChain(
        llm=llm,
        verbose=True,
        memory=memory,
        prompt=system_prompt,
    )

    response = conversation.predict(input=message)
    return Response({'message': response, 'session_id': session_id})

@api_view(('POST',))
@renderer_classes((JSONRenderer,))
@permission_classes((HasAPIKey,))
def add_user(request):
    body = json.loads(request.body)
    email = body['email']
    name = body['name']
    preferred_name = body['preferred_name']
    initial_session_id = str(uuid.uuid4())
    user = User(name=name, email=email, preferred_name=preferred_name, initial_session_id=initial_session_id)
    user.save()
    return Response({'user_id': user.id, 'session_id': initial_session_id})