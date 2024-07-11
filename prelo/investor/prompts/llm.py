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
    {
        "name": "recommendation_analysis",
        "description": "make a recommendation to an investor based on the analysis of a pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "score": {
                    "type": "number",
                    "description": "The score of the company's investment potential from 1 to 100 based on the company analysis and the investor's thesis"
                },
                "reason": {
                    "type": "string",
                    "description": "Why the company outlined in the deck matches the thesis or why it does not"

                },
                "matches": {
                    "type": "boolean",
                    "description": "Whether or not the company matches the investment thesis",
                },
            },
            "required": ["matches", "reason", "score"],
        },
    },
    {
        "name": "concerns_analysis",
        "description": "identify the top 5 concerns an investor might have about a company based on the pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "concerns": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "concern": {
                                "type": "string",
                                "description": "The concern an investor might have"
                            },
                            "title": {
                                "type": "string",
                                "description": "The title of the concern"
                            }
                        }
                    },
                }

            },
            "description": "The top 5 concerns an investor might have about the company"
        },
    },
    {
        "name": "recommended_next_step",
        "description": "provide the recommended next step for an investor based on the analysis of a pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "next_step_id": {
                    "type": "string",
                    "description": "The id of the recommended next step for the investor"
                },
                "next_step_description": {
                    "type": "string",
                    "description": "The description of the recommended next step for the investor"
                }
            },
            "required": ["next_step_id", "next_step_description"],
        },
    }

]
