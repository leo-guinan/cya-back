from backend.celery import app
from prelo.aws.s3_utils import file_exists
from prelo.models import PitchDeck
from prelo.pitch_deck.analysis import analyze_pitch_deck


@app.task(name="prelo.tasks.check_for_decks")
def check_for_decks():
    decks = PitchDeck.objects.filter(status=PitchDeck.CREATED).all()
    for deck in decks:
        # check s3 path to see if a file exists yet
        # if it does, change status to UPLOADED
        if file_exists(deck.s3_path):
            deck.status = PitchDeck.UPLOADED
            deck.save()
            process_deck.delay(deck.id)


@app.task(name="prelo.tasks.process_deck")
def process_deck(deck_id):
    deck = PitchDeck.objects.get(id=deck_id)
    # process the deck
    deck.status = PitchDeck.PROCESSING
    deck.save()
    analyze_pitch_deck(deck)
