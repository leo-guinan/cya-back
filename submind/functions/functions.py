functions = [
    {
        "name": "research_questions",
        "description": "decide what to research based on a thought from the founder",
        "parameters": {
            "type": "object",
            "properties": {
                "research": {
                    "type": "object",
                    "description": "What research needs to be done",
                    "properties": {
                        "research_questions": {
                            "type": "array",
                            "description": "The questions you want to answer with your research",
                            "items": {
                                "type": "string"
                            }
                        },
                        "summary": {
                            "type": "string",
                            "description": "A summary of what you are researching and why you think it would be helpful for the user."
                        }

                    }
                },
            },
            "required": ["research"],
        },
    },
    {
        "name": "delegate_to_subminds",
        "description": "decide what you need to know and delegate those questions to your subminds ",
        "parameters": {
            "type": "object",
            "properties": {
                "delegated_questions": {
                    "type": "array",
                    "description": "What questions you need to answer in order to accomplish your goal",
                    "items": {
                        "type": "object",
                        "properties": {
                            "question": {"type": "string", "description": "The question you have"},
                            "subminds": {
                                "type": "array",
                                "description": "Which subminds should answer the question",
                                "items": {
                                    "type": "object",
                                    "description": "Which submind to delegate the question to",
                                    "properties": {
                                        "submind_id": {"type": "string", "description": "The id of the submind"},
                                        "submind_name": {"type": "string", "description": "The name of the submind"},
                                        "submind_description": {"type": "string",
                                                                "description": "The description of the submind"}
                                    }
                                }

                            }
                        }

                    },
                },
            },
            "required": ["delegated_questions"],
        },
    }
]
