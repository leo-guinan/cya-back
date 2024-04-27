from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from backend.celery import app
from prelo.aws.s3_utils import file_exists
from prelo.models import PitchDeck, PitchDeckAnalysis
from prelo.pitch_deck.analysis import analyze_deck
from prelo.pitch_deck.processing import prep_deck_for_analysis
from prelo.pitch_deck.reporting import combine_into_report


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

@app.task(name="prelo.tasks.check_for_analysis")
def check_for_analysis():
    decks_to_analyze = PitchDeckAnalysis.objects.filter(deck__status=PitchDeck.READY_FOR_ANALYSIS).all()
    for deck_analysis in decks_to_analyze:
        analyze_deck_task.delay(deck_analysis.id)

@app.task(name="prelo.tasks.check_for_reporting")
def check_for_reporting():
    decks_to_report = PitchDeckAnalysis.objects.filter(deck__status=PitchDeck.READY_FOR_REPORTING).all()
    for deck_analysis in decks_to_report:
        create_report_for_deck.delay(deck_analysis.id)


@app.task(name="prelo.tasks.create_report_for_deck")
def create_report_for_deck(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.REPORTING
    pitch_deck_analysis.deck.save()
    report = combine_into_report(pitch_deck_analysis)
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                {"type": "deck.status.update", "message": report,
                                                 "id": pitch_deck_analysis.deck.id, "status": pitch_deck_analysis.deck.status})
        scores = pitch_deck_analysis.deck.company.scores.first()
        score_object = {
            'market': {
                'score': scores.market_opportunity,
                'reason': scores.market_reasoning
            },
            'team': {
                'score': scores.team,
                'reason': scores.team_reasoning
            },
            'founder': {
                'score': scores.founder_market_fit,
                'reason': scores.founder_market_reasoning
            },
            'product': {
                'score': scores.product,
                'reason': scores.product_reasoning
            },
            'traction': {
                'score': scores.traction,
                'reason': scores.traction_reasoning

            },
            'final': {
                'score': scores.final_score,
                'reason': scores.final_reasoning
            }
        }
        async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                {"type": "deck.score.update", "message": report,
                                                 "id": pitch_deck_analysis.deck.id, "scores": score_object})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return

@app.task(name="prelo.tasks.analyze_deck")
def analyze_deck_task(pitch_deck_analysis_id: int):
    pitch_deck_analysis = PitchDeckAnalysis.objects.get(id=pitch_deck_analysis_id)
    pitch_deck_analysis.deck.status = PitchDeck.ANALYZING
    pitch_deck_analysis.deck.save()
    analyze_deck(pitch_deck_analysis)
    create_report_for_deck.delay(pitch_deck_analysis.id)
    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(pitch_deck_analysis.deck.uuid,
                                                {"type": "deck.status.update", "message": "Deck analyzed. Writing report",
                                                 "id": pitch_deck_analysis.deck.id, "status": pitch_deck_analysis.deck.status})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return



@app.task(name="prelo.tasks.process_deck")
def process_deck(deck_id):
    deck = PitchDeck.objects.get(id=deck_id)
    # process the deck
    deck.status = PitchDeck.PROCESSING
    deck.save()
    analysis = prep_deck_for_analysis(deck)

    analyze_deck_task.delay(analysis.id)

    try:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(deck.uuid,
                                                {"type": "deck.status.update", "message": "Deck processed. Beginning analysis.",
                                                 "id": deck.id, "status": deck.status})
    except Exception as e:
        print(e)
        # not vital, just try to return response to chat if possible.
    return