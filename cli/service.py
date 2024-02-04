from cli.models import State


def get_state_for_session(session_id):
    state = State.objects.filter(session_id=session_id).first()
    if not state:
        state = State.objects.create(session_id=session_id, state="{}")
    return state