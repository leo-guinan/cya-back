from backend.celery import app
from django.db.models import Q
from submind.communicate.communicate import answer_submind, ask_submind
from submind.delegation.delegation import delegate
from submind.memory.memory import remember
from submind.models import Goal
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

    delegated_questions = delegate(goal)

    for question in delegated_questions:
        for delegated_to in question['subminds']:
            print(f'delegating question {question["question"]} to submind {delegated_to["submind_name"]}')
            new_goal_id = ask_submind(delegated_to['submind_id'], question['question'], fast=goal.fast)
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
