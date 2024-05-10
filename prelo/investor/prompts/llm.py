THESIS_MATCH = """ You are a thesis matching submind for an early stage investor.

Here's the thesis you are matching against: {thesis}

Here's the pitch deck you received: {deck}

Determine whether or not the thesis matches, and explain how it matches or why it does not, and provide a score from 0-100 on how closely the company matches the thesis.

"""

functions = [
    {
        "name": "match_thesis",
        "description": "determine whether a company matches an investor's thesis based on their pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "matches": {
                    "type": "boolean",
                    "description": "Whether or not the company matches the investment thesis",
                },
                "reason": {
                    "type": "string",
                    "description": "Why the company outlined in the deck matches the thesis or why it does not"

                },
                "score": {
                    "type": "string",
                    "description": "The score of the match between the company and the thesis from 0-100"
                }
            },
            "required": ["matches", "reason", "score"],
        },
    },
]
