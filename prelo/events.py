import requests
from decouple import config


def record_prelo_event(data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": config('TELEMETRY_API_KEY')
    }
    requests.post(f"{config('TELEMETRY_BASE_URL')}/log",
                  headers=headers,
                  json={
                      "data": data,
                      "table": config('PRELO_TELEMETRY_TABLE')
                  }
                  )


def record_smd_event(data):
    headers = {
        "Content-Type": "application/json",
        "Authorization": config('TELEMETRY_API_KEY')
    }
    requests.post(f"{config('TELEMETRY_BASE_URL')}/log",
                  headers=headers,
                  json={
                      "data": data,
                      "table": config('SCORE_MY_DECK_TELEMETRY_TABLE')
                  }
                  )
