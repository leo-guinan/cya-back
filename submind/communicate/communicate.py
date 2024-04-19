import uuid

from submind.memory.memory import remember, learn
from submind.models import Goal, Submind, Question
from submind.research.research import research


def ask_submind(submind_id:int, question: str, client_id: int):
    new_goal = Goal()
    new_goal.content = f'Answer the question: {question}'
    new_goal.submind_id = submind_id
    new_goal.uuid = str(uuid.uuid4())
    new_goal.client_id = client_id
    new_goal.save()
    return new_goal.id

def answer_submind(goal: Goal):
    answer = research(goal)
    learn(goal.client.id,{"question": goal.content, "answer": answer}, goal.submind)




