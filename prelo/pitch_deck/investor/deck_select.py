from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory

from prelo.chat.history import get_prelo_message_history
from prelo.models import PitchDeck
from prelo.prompts.functions import functions
from prelo.prompts.prompts import DECK_SELECTION_PROMPT
from submind.llms.submind import SubmindModelFactory
from langchain_core.output_parsers.openai_functions import JsonKeyOutputFunctionsParser


def identify_pitch_deck_to_use(investor_id, conversation_uuid, message):
    decks = PitchDeck.objects.filter(user_id=investor_id).all()
    if not decks:
        return None
    if len(decks) == 1:
        return decks[0]
    combined_decks = ""
    for deck in decks:
        combined_decks += f"UUID: {deck.uuid} | Name: {deck.name}\n"

    model = SubmindModelFactory.get_model(conversation_uuid, "deck_select")
    select_deck_prompt = ChatPromptTemplate.from_template(DECK_SELECTION_PROMPT)
    investor_runnable = select_deck_prompt | model.bind(function_call={"name": "deck_select"},
                                                        functions=functions) | JsonKeyOutputFunctionsParser(key_name="result")


    history = get_prelo_message_history(f'custom_claude_{conversation_uuid}')

    combined_history = "\n".join(list(map(lambda x: f'Type: {x.type} - Message: {x.content}', history.messages)))
    print(f'combined_history: {combined_history}')
    print(f"history message: {history.messages}")
    print(f"History history: {history.get_session_history()}")
    investor_answer = investor_runnable.invoke({
        "decks": combined_decks,
        "message": message,
        "history": combined_history
    })

    return decks.filter(uuid=investor_answer["deck_uuid"]).first()
