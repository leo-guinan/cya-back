from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from decouple import config
from django.db.models import Q
from backend.celery import app
from submind.communicate.communicate import answer_submind, ask_submind
from submind.delegation.delegation import delegate
from submind.delegation.tools import determine_tools, run_tools
from submind.memory.memory import remember
from submind.models import Goal
from submind.overrides.mongodb import MongoDBChatMessageHistoryOverride
from submind.tools.answers import compile_answers


@app.task(name="submind.tasks.think")
def think(goal_id: int):
    """
    Think about a goal
    """
    goal = Goal.objects.get(id=goal_id)

    if len(goal.submind.subminds.all()) == 0:
        answer_submind(goal)
        return
    tools_to_run = determine_tools(goal)

    tool_info = run_tools(tools_to_run)

    delegated = delegate(goal, tool_info)
    print(delegated)
    delegated_questions = delegated.get('delegated_questions', [])
    if delegated.get('answer', ''):
        goal.completed = True
        goal.results = delegated['answer']
        goal.save()
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
        for delegated_to in question['subminds']:
            print(f'delegating question {question["question"]} to submind {delegated_to["submind_name"]}')
            new_goal_id = ask_submind(delegated_to['submind_id'], question['question'],
                                      extra_data=question.get('extra_data', ""), fast=goal.fast)
            think.delay(new_goal_id)


@app.task(name="submind.tasks.complete_goals")
def complete_goals():
    goals = Goal.objects.filter(Q(results='') | Q(results__isnull=True)).all()
    print(f'found {len(goals)} goals')
    for goal in goals:
        if goal.is_complete():
            print(f'completing goal {goal.id}')
            complete_goal.delay(goal.id)


@app.task(name="submind.tasks.complete_goal")
def complete_goal(goal_id: int):
    goal = Goal.objects.get(id=goal_id)
    questions = goal.questions.all()
    results = []
    for question in questions:
        results.extend(question.thoughts.all())
    mind = remember(goal.submind, goal.client_id)

    result = compile_answers(results, goal.submind, mind, goal.content)
    goal.results = result
    goal.save()

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
