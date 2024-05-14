import time
import uuid

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.db.models import Q
from langchain_core.output_parsers import StrOutputParser
from langchain_core.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from backend.celery import app
from prelo.models import PitchDeck
from prelo.prompts.prompts import CHAT_WITH_DECK_SYSTEM_PROMPT
from submind.communicate.communicate import answer_submind, ask_submind
from submind.delegation.delegation import delegate, spawn_children
from submind.functions.functions import functions
from submind.llms.submind import SubmindModelFactory
from submind.memory.memory import remember, learn
from submind.models import Goal, Submind, Conversation, Message
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride
from submind.prompts.prompts import START_CONVERSATION_PROMPT, SUBMIND_CONVERSATION_RESPONSE, CAN_I_HELP_PROMPT
from submind.tools.answers import compile_thought_answers, compile_goal_answers


@app.task(name="submind.tasks.think")
def think(goal_id: int, shallow=True):
    """
    Think about a goal
    """
    goal = Goal.objects.get(id=goal_id)
    print(f'thinking about goal {goal.content}')
    if len(goal.submind.subminds.all()) == 0:
        print("Answering submind directly because no child subminds.")
        answer_submind(goal)
        return
    # tools_to_run = determine_tools(goal)
    #
    # tool_info = run_tools(tools_to_run)
    tool_info = ""
    delegated = delegate(goal, tool_info, shallow)
    delegated_questions = delegated.get('delegated_questions', [])
    if shallow and delegated.get('answer', ''):
        print("Shallow and have answer instead of delegating.")
        goal.completed = True
        goal.results = delegated['answer']
        if delegated.get('supporting_data', ''):
            goal.supporting_data = delegated['supporting_data']
        goal.save()
        if goal.client:
            # need to add the result to the chat history regardless of whether the chat is still active
            message_history = MongoDBChatMessageHistoryOverride(
                connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
                session_id=f'{goal.client.uuid}{goal.client.session_suffix}',
                database_name=goal.client.database_name,
                collection_name=goal.client.collection_name
            )
            message_history.add_ai_message(delegated['answer'])

            try:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(goal.client.uuid,
                                                        {"type": "chat.message", "message": delegated['answer'],
                                                         "id": goal.id})
            except Exception as e:
                print(e)
                # not vital, just try to return response to chat if possible.
        return

    for question in delegated_questions:
        for delegated_to in question.get('subminds', []):
            print(f'delegating question {question["question"]} to submind {delegated_to["submind_name"]}')
            new_goal = ask_submind(delegated_to['submind_id'], question['question'],
                                      extra_data=question.get('extra_data', ""), fast=goal.fast)

            new_goal.delegated_from = goal

            new_goal.save()
            think(new_goal.id, shallow=shallow)


@app.task(name="submind.tasks.create_structure")
def create_structure(name:str, intent: str, parent_id=int, level=0):
    """
    Think about a goal
    """
    submind = Submind.objects.create(name=name, description=intent, uuid=str(uuid.uuid4()),
                                     mindUUID=str(uuid.uuid4()))

    parent = Submind.objects.get(id=parent_id)
    parent.subminds.add(submind)
    parent.save()
    goal = Goal.objects.create(content=f"Learn everything you can about {intent}", submind=submind,
                               uuid=str(uuid.uuid4()))

    if level > 1:
        return

    kids = spawn_children(goal, submind)

    for kid in kids:
        create_structure(kid['submind_name'], kid['submind_description'], submind.id, level + 1)
    return

    # print(delegated)
    # delegated_questions = delegated.get('delegated_questions', [])
    # if delegated.get('answer', ''):
    #     goal.completed = True
    #     goal.results = delegated['answer']
    #     goal.save()
    #     # need to add the result to the chat history regardless of whether the chat is still active
    #     message_history = MongoDBChatMessageHistoryOverride(
    #         connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
    #         session_id=f'{goal.client.uuid}{goal.client.session_suffix}',
    #         database_name=goal.client.database_name,
    #         collection_name=goal.client.collection_name
    #     )
    #     message_history.add_ai_message(delegated['answer'])
    #
    #     try:
    #         channel_layer = get_channel_layer()
    #         async_to_sync(channel_layer.group_send)(goal.client.uuid,
    #                                                 {"type": "chat.message", "message": delegated['answer'],
    #                                                  "id": goal.id})
    #     except Exception as e:
    #         print(e)
    #         # not vital, just try to return response to chat if possible.
    #     return
    #
    # for question in delegated_questions:
    #     for delegated_to in question['subminds']:
    #         print(f'delegating question {question["question"]} to submind {delegated_to["submind_name"]}')
    #         new_goal_id = ask_submind(delegated_to['submind_id'], question['question'],
    #                                   extra_data=question.get('extra_data', ""), fast=goal.fast)
    #         think.delay(new_goal_id)


@app.task(name="submind.tasks.complete_goals")
def complete_goals():
    goals = Goal.objects.filter(Q(results='') | Q(results__isnull=True)).all()
    print(f'found {len(goals)} goals')
    for goal in goals:
        if goal.is_complete():
            print(f'completing goal {goal.id}')
            complete_goal(goal.id)


@app.task(name="submind.tasks.learn_something")
def learn_something(question, answers, submind_id):
    submind = Submind.objects.get(id=submind_id)
    learn({"question": question, "answer": "\n".join(answers)}, submind)


@app.task(name="submind.tasks.complete_goal")
def complete_goal(goal_id: int):
    goal = Goal.objects.get(id=goal_id)
    questions = goal.questions.all()
    results = []
    if len(questions) > 0:

        for question in questions:
            print(f'question {question.content} has {len(question.thoughts.all())} thoughts')
            results.extend(question.thoughts.all())
            learn_something(question.content, [thought.content for thought in question.thoughts.all()],
                                  goal.submind.id)
        mind = remember(goal.submind)

        result = compile_thought_answers(results, goal.submind, mind, goal.content)
        goal.results = result
        goal.save()
    else:
        delegated_questions = goal.delegated_goals.all()
        for question in delegated_questions:
            results.append({"question": question.content, "answer": question.results})
            learn_something(question.content, [question.results], goal.submind.id)
        mind = remember(goal.submind)
        result = compile_goal_answers(results, goal.submind, mind, goal.content)
        goal.results = result
        goal.save()

    if goal.client:
        # need to add the result to the chat history regardless of whether the chat is still active
        message_history = MongoDBChatMessageHistoryOverride(
            connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
            session_id=f'{goal.client.uuid}{goal.client.session_suffix}',
            database_name=goal.client.database_name,
            collection_name=goal.client.collection_name
        )
        message_history.add_ai_message(result)

        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(goal.client.uuid,
                                                    {"type": "chat.message", "message": result, "id": goal.id})
        except Exception as e:
            print(e)
            # not vital, just try to return response to chat if possible.
            pass


def get_message_history(session_id: str) -> MongoDBChatMessageHistoryOverride:
    return MongoDBChatMessageHistoryOverride(
        connection_string=config('MAC_MONGODB_CONNECTION_STRING'),
        session_id=f'{session_id}_chat',
        database_name=config("SCORE_MY_DECK_DATABASE_NAME"),
        collection_name=config("SCORE_MY_DECK_COLLECTION_NAME")
    )


@app.task(name="submind.tasks.chat")
def chat(goal_id: int):
    start_time = time.perf_counter()
    goal = Goal.objects.get(id=goal_id)
    # Needs a submind to chat with. How does this look in practice?
    # Should have tools to pull data, knowledge to respond from, with LLM backing.
    model = SubmindModelFactory.get_model(goal.submind.uuid, "chat")
    # should it use the submind at the point of the initial conversation? Or auto upgrade as the mind learns more?
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                CHAT_WITH_DECK_SYSTEM_PROMPT
            ),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}"),
        ]
    )
    runnable = prompt | model

    with_message_history = RunnableWithMessageHistory(
        runnable,
        get_message_history,
        input_messages_key="input",
        history_messages_key="history",
    )
    pitch_deck = PitchDeck.objects.filter(uuid=goal.client.uuid).first()
    submind_document = remember(goal.submind)
    answer = with_message_history.invoke(
        {
            "input": goal.content,
            "values": submind_document,
            "thesis": "",
            "deck": pitch_deck.analysis.compiled_slides,
            "analysis": pitch_deck.analysis.extra_analysis,
        },
        config={"configurable": {"session_id": goal.client.uuid}},

    )
    end_time = time.perf_counter()
    print(f"Chat took {end_time - start_time} seconds")
    goal.results = answer.content
    goal.completed = True
    goal.save()
    print(answer.content)



@app.task(name="submind.tasks.receive_messages")
def receive_messages():
    messages = Message.objects.filter(received=False).all()
    print(f"found {len(messages)} messages to receive...\n\n")
    for message in messages:
        model = SubmindModelFactory.get_model(message.sender.uuid, "receive_message")
        prompt = ChatPromptTemplate.from_template(CAN_I_HELP_PROMPT)
        chain = prompt | model.bind(function_call={"name": "can_I_help"},
                                    functions=functions) | JsonOutputFunctionsParser()

        from_submind = message.sender
        receiving_submind = message.receiver

        if receiving_submind == message.conversation.initiated_by:
            receiving_mind = remember(receiving_submind)
            learn({"question": message.conversation.topic, "answer": message.content}, receiving_submind)
            receiving_mind = remember(receiving_submind)
            message.received = True
            message.save()
            return
        receiving_mind = remember(receiving_submind)
        prepped_subminds = []
        for child in receiving_submind.subminds.all():
            prepped_subminds.append(
                f"Submind -- Id: {child.id} -- Name: {child.name} -- Description: {child.description}")
        response = chain.invoke(
            {"description": receiving_submind.description,
             "subminds": "\n".join(prepped_subminds),
             "topic":message.content,
             "mind": receiving_mind
             })

        if response['can_i_help']:
            print(f"Receiving submind, submind {receiving_submind.name}, has {len(prepped_subminds)} children. Delegating...\n\n")
            if len(prepped_subminds) == 0:
                print("responding...\n\n")
                # determine whether or not should try to learn or should answer from memory. Alternate question: how much do I actually need to learn? Or at this level, is simply the specificity enought?
                respond_prompt = ChatPromptTemplate.from_template(SUBMIND_CONVERSATION_RESPONSE)
                response_chain = respond_prompt | model | StrOutputParser()
                answer = response_chain.invoke(
                    {"description": receiving_submind.description,
                     "topic":message.content,
                     "mind": receiving_mind
                     })
                Message.objects.create(uuid=str(uuid.uuid4()), content=answer, sender=receiving_submind, receiver=from_submind, conversation=message.conversation)


            else:
                print(f"Starting a new conversation with children")
                passed_along = ask_children(receiving_submind.id, message.content, message.conversation.id)
        else:
            print("Can't help, bailing...\n\n")

        message.received = True
        message.save()
    finalize_conversations.delay()




@app.task(name="submind.tasks.ask_child_subminds")
def ask_children(submind_id, topic, previous_conversation_id=None):
    base_submind = Submind.objects.get(id=submind_id)
    model = SubmindModelFactory.get_model(base_submind.uuid, "start_conversation")

    prompt = ChatPromptTemplate.from_template(START_CONVERSATION_PROMPT)
    chain = prompt | model.bind(function_call={"name": "start_conversations"},
                                functions=functions) | JsonOutputFunctionsParser()

    mind = remember(base_submind)

    prepped_subminds = []
    for child in base_submind.subminds.all():
        prepped_subminds.append(
            f"Submind -- Id: {child.id} -- Name: {child.name} -- Description: {child.description}")

    response = chain.invoke(
        {"description": base_submind.description,
         "subminds": "\n".join(prepped_subminds),
         "topic": topic,
         "mind": mind
         })

    new_conversation = Conversation.objects.create(uuid=str(uuid.uuid4()), topic=topic, initiated_by=base_submind)
    if previous_conversation_id:
        previous_conversation = Conversation.objects.get(id=previous_conversation_id)
        new_conversation.parent = previous_conversation
        new_conversation.save()

    messages = []
    for conversation in response["conversations"]:
        try:
            to_submind = Submind.objects.get(id=conversation["submind_id"])
            new_conversation.participants.add(to_submind)
            new_conversation.save()
            msg = Message.objects.create(uuid=str(uuid.uuid4()), content=conversation["conversation_topic"],
                                         sender=base_submind, receiver=to_submind, conversation=new_conversation)
            messages.append(msg)
        except Exception as e:
            print(e)
            print(f'Error with submind id: {conversation.get("submind_id", "Missing submind id")}')
            continue

    receive_messages.delay()

@app.task(name="submind.tasks.finalize_conversations")
def finalize_conversations():
    conversations_to_finalize = Conversation.objects.filter(completed=False).all()
    print(f"found {len(conversations_to_finalize)} conversations to finalize...\n\n")
    for conversation in conversations_to_finalize:
        model = SubmindModelFactory.get_model(conversation.initiated_by.uuid, "finalize_conversation")

        finished = True
        for blocking in conversation.blocked_by.all():
            print(f"Checking blocking conversation {blocking.id} to see if finished...")
            if not blocking.completed:
                print("Not finished, bailing...")
                finished = False
        if not finished:
            continue
        for participant in conversation.participants.all():
            received_from = Message.objects.filter(conversation=conversation, sender=participant).first()
            if not received_from:
                print(
                    f"Looks like conversation {conversation.id} hasn't received any messages yet from {participant.id}...\n\n")
                finished = False
                break
        if not finished:
            continue
        # ok, at this point, we know this conversation is finished. So we have learned from all the sub conversations and need to see if this is blocking any upstairs conversations, and respond to that sender.
        conversation.finished = True
        conversation.save()
        if conversation.parent:
            # get any messages that have not been responded to in that conversation from this conversation's initiator
            outstanding_messages = Message.objects.filter(conversation=conversation.parent,
                                                          receiver=conversation.initiated_by, received=True).all()
            for msg in outstanding_messages:
                print("Now responding to outstanding message...\n\n")
                respond_prompt = ChatPromptTemplate.from_template(SUBMIND_CONVERSATION_RESPONSE)
                response_chain = respond_prompt | model | StrOutputParser()
                mind = remember(conversation.initiated_by)
                answer = response_chain.invoke(
                    {"description": conversation.initiated_by.description,
                     "topic": msg.content,
                     "mind": mind
                     })
                # print(answer)
                Message.objects.create(uuid=str(uuid.uuid4()), content=answer, sender=msg.receiver, receiver=msg.sender,
                                       conversation=msg.conversation)