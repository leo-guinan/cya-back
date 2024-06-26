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
        "name": "spawn_subminds",
        "description": "determine which subminds to spawn based on what you want to learn",
        "parameters": {
            "type": "object",
            "properties": {
                "subminds": {
                    "type": "array",
                    "description": "The subminds you want to spawn",
                    "items": {
                        "type": "object",
                        "properties": {
                            "submind_name": {"type": "string", "description": "A name for the submind"},
                            "submind_description": {"type": "string",
                                                    "description": "The topic the submind should focus on learning about"},
                        }
                    }
                }
            },
            "required": ["subminds"],
        }
    },
    {
        "name": "answer_and_skip_delegation",
        "description": "Answer as well as you can with data to back up your answer",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the question you were asked"
                },
                "supporting_data": {
                    "type": "string",
                    "description": "The data you have that supports your answer"
                }
            },
            "required": ["answer"],
        },
    },
    {
        "name": "delegate_to_subminds",
        "description": "decide what you need to know and delegate those questions to your subminds ",
        "parameters": {
            "type": "object",
            "properties": {
                "answer": {
                    "type": "string",
                    "description": "The answer to the question you were asked"
                },
                "delegated_questions": {
                    "type": "array",
                    "description": "What questions you need to answer in order to accomplish your goal",
                    "items": {
                        "type": "object",
                        "properties": {

                            "question": {"type": "string", "description": "The question you have"},
                            "extra_data": {
                                "type": "string",
                                "description": "The extra data you have that might help answer the question"
                            },
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
    },
    {
        "name": "determine_tools_to_run",
        "description": "decide which tools to run and what data to get from each tool",
        "parameters": {
            "type": "object",
            "properties": {
                "tools_needed": {
                    "type": "array",
                    "description": "What questions you need to answer in order to accomplish your goal",
                    "items": {
                        "type": "object",
                        "properties": {
                            "tool_name": {"type": "string", "description": "the name of the tool to run"},
                            "query": {
                                "type": "string",
                                "description": "what data you need to get from the tool"
                            },
                            "data_to_send": {
                                "type": "string",
                                "description": "what data you need to send to the tool"
                            }
                        }

                    },
                },
            },
            "required": ["tools_needed"],
        },
    },
    {
        "name": "start_conversations",
        "description": "decide which subminds to start conversations with",
        "parameters": {
            "type": "object",
            "properties": {
                "conversations": {
                    "type": "array",
                    "description": "which conversations to have",
                    "items": {
                        "type": "object",
                        "properties": {
                            "submind_id": {
                                "type": "string",
                                "description": "The id of the submind you want to have a conversation with.",

                            },
                            "conversation_topic": {
                                "type": "string",
                                "description": "A summary of what you are researching and why you think it would be helpful for the user."
                            }

                        }

                    }
                },
            },
            "required": ["conversations"],
        },
    },
    {
        "name": "can_I_help",
        "description": "decide whether or not you are able to respond to the request knowledgably",
        "parameters": {
            "type": "object",
            "properties": {
                "can_i_help": {
                    "type": "boolean",
                    "description": "am I able to help with this request",

                },
            },
            "required": ["can_i_help"],
        },
    },
]
