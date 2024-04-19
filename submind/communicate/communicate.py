import uuid

from submind.memory.memory import learn
from submind.models import Goal
from submind.research.remember import answer_from_memory
from submind.research.research import research


def ask_submind(submind_id:int, question: str, fast: bool):
    new_goal = Goal()
    new_goal.content = f'Answer the question: {question}'
    new_goal.submind_id = submind_id
    new_goal.uuid = str(uuid.uuid4())
    new_goal.fast = fast
    new_goal.save()
    return new_goal.id

def answer_submind(goal: Goal):
    if not goal.fast:
        answer = research(goal)
    else:
        answer = answer_from_memory(goal)
    learn(goal.client.id if goal.client else None,{"question": goal.content, "answer": answer}, goal.submind)




