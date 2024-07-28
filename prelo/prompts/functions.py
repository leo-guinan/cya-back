functions = [
    {
        "name": "extract_promo_info",
        "description": "identify and remove promotional material related to the tools used to create a pitch deck",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "promotional_info": {
                            "type": "string",
                            "description": "The promotional information identified",
                        },
                        "clean_info": {
                            "type": "string",
                            "description": "The starting info without any of the promotional info"
                        }

                    }
                },
            },
            "required": ["results"],
        },
    },
    {
        "name": "risk_breakdown",
        "description": "identify the risks, objections, and ways to de-risk a company for investment",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the risk analysis",
                    "properties": {
                        "top_risk": {
                            "type": "string",
                            "description": "The biggest risk to the company",
                        },
                        "objections_to_overcome": {
                            "type": "string",
                            "description": "The biggest objections to the company",
                        },
                        "how_to_de_risk": {
                            "type": "string",
                            "description": "The best ways to de-risk the company",
                        },

                    }
                },
            },
            "required": ["results"],
        },
    },
    {
        "name": "extract_company_info",
        "description": "identify information about the company pitching the investor",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "company_name": {
                            "type": "string",
                            "description": "the name of the company",
                        },
                        "team": {
                            "type": "array",
                            "description": "The team members of the company",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "name": {
                                        "type": "string",
                                        "description": "The name of the team member"
                                    },
                                    "role": {
                                        "type": "string",
                                        "description": "The role of the team member"
                                    },
                                    "background": {
                                        "type": "string",
                                        "description": "The background of the team member"
                                    },
                                    "founder": {
                                        "type": "boolean",
                                        "description": "Whether the team member is a founder"
                                    }
                                }
                            }
                        },
                        "industry": {
                            "type": "string",
                            "description": "The industry of the company"
                        },
                        "problem": {
                            "type": "string",
                            "description": "the problem the company is solving"
                        },
                        "solution": {
                            "type": "string",
                            "description": "the company's solution to the problem"
                        },
                        "market_size": {
                            "type": "string",
                            "description": "The estimated market size the company is targeting"
                        },
                        "traction": {
                            "type": "string",
                            "description": "the company's traction so far"
                        },
                        "revenue": {
                            "type": "string",
                            "description": "The company's revenue"
                        },
                        "why_now": {
                            "type": "string",
                            "description": "Why the company should exist now"
                        },
                        "domain_expertise": {
                            "type": "string",
                            "description": "what special expertise the founder/team have that will help them solve this problem"
                        },
                        "founder_contact": {
                            "type": "string",
                            "description": "Contact Info for the founder"
                        },
                        "founding_date": {
                            "type": "string",
                            "description": "The approximate date the company was founded"
                        },
                        "location": {
                            "type": "string",
                            "description": "where the company is based"
                        },
                        "funding_round": {
                            "type": "string",
                            "description": "The current funding round the company is raising"
                        },
                        "funding_amount": {
                            "type": "string",
                            "description": "The amount of money the company wants to raise"
                        },
                        "competition": {
                            "type": "string",
                            "description": "The company's competition"
                        },
                        "partnerships": {
                            "type": "string",
                            "description": "The company's partnerships"
                        },
                        "founder_market_fit": {
                            "type": "string",
                            "description": "The founder's market fit"
                        },

                    }
                },
            },
            "required": ["results"],
        },
    },
    {
        "name": "calculate_score_for_category",
        "description": "score a company on a specific category",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "category": {
                            "type": "string",
                            "description": "the category being scored",
                        },
                        "score": {
                            "type": "number",
                            "description": "The score of the company in the category"
                        },
                        "reasoning": {
                            "type": "string",
                            "description": "The reasoning behind the score"
                        },
                        "rubric": {
                            "type": "string",
                            "description": "the scoring according to the provided rubric"
                        }
                    }
                },
            }
        },
    },
    {
        "name": "calculate_company_score",
        "description": "score the company on several categories to determine investment potential",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of analysis",
                    "properties": {
                        "market": {
                            "type": "object",
                            "description": "the score of the market opportunity",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the market opportunity"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The breakdown of the score according to the rubric"
                                }
                            }
                        },
                        "team": {
                            "type": "object",
                            "description": "the score of the team",

                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the team"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The breakdown of the score according to the rubric"
                                }
                            }

                        },
                        "founder_fit": {
                            "type": "object",
                            "description": "the score of the founder/market fit",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the founder fit"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The breakdown of the score according to the rubric"
                                }
                            }
                        },

                        "traction": {
                            "type": "object",
                            "description": "the score of the company's traction",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the company's traction"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The breakdown of the score according to the rubric"
                                }
                            }
                        },
                        "product": {
                            "type": "object",
                            "description": "the score of the company's product",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the company's product"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The reasoning behind the score"
                                }
                            }
                        },
                        "final_score": {
                            "type": "object",
                            "description": "the final score of the company",
                            "properties": {
                                "score": {
                                    "type": "number",
                                    "description": "The score of the company"
                                },
                                "reasoning": {
                                    "type": "string",
                                    "description": "The investment recommendation based on the score."
                                }
                            }
                        },
                    }
                },
            },
            "required": ["results"],
        },
    },
    {
        "name": "lookup_pitch_deck_uuid",
        "description": "identify the uuid in the message",
        "parameters": {
            "type": "object",
            "properties": {
                "uuid": {
                    "type": "string",
                    "description": "the uuid of the pitch deck to lookup",

                },
            },
            "required": ["uuid"],
        },
    },
    {
        "name": "lookup_pitch_deck_uuid_and_slide_numbers",
        "description": "identify the uuid in the message and the slide numbers of the requested slides",
        "parameters": {
            "type": "object",
            "properties": {
                "uuid": {
                    "type": "string",
                    "description": "the uuid of the pitch deck to lookup",

                },
                "slide_numbers": {
                    "type": "array",
                    "description": "the slide numbers requested",
                    "items": {
                        "type": "number"
                    }
                }
            },
            "required": ["uuid", "slide_numbers"],
        },
    },
    {
        "name": "choose_path",
        "description": "identify whether or not one of your tools can be used",
        "parameters": {
            "type": "object",
            "properties": {
                "use_tool": {
                    "type": "boolean",
                    "description": "whether or not to use a tool",

                },
                "tool_id": {
                    "type": "string",
                    "description": "the id of the tool to use if one is chosen",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "create_gtm_strategy",
        "description": "create a go-to-market strategy for a company",
        "parameters": {
            "type": "object",
            "properties": {

                "strategy": {
                    "type": "object",
                    "description": "The go-to-market strategy for the company",
                    "properties": {
                        "suggestions": {
                            "type": "array",
                            "description": "The suggestions for the go-to-market strategy",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "step": {
                                        "type": "string",
                                        "description": "The step in the strategy"
                                    },
                                    "description": {
                                        "type": "string",
                                        "description": "The description of the step"
                                    }
                                }
                            }
                        }
                    }
                },
                "competitors": {
                    "type": "array",
                    "description": "The company's competitors",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "The name of the competitor"
                            },
                            "strategy": {
                                "type": "string",
                                "description": "The competitor's go-to-market strategy"
                            }
                        }
                    }

                },
            },
            "required": ["strategy", "competitors"],
        },
    },
    {
        "name": "founder_linkedin_extraction",
        "description": "extract the linkedin information of a founder",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the linkedin extraction",
                    "properties": {
                        "linkedin_url": {
                            "type": "string",
                            "description": "The linkedin url of the founder",
                        },
                        "linkedin_info": {
                            "type": "string",
                            "description": "The linkedin information of the founder"
                        }

                    }
                },
            },
            "required": ["results"],
        }
    },
    {
        "name": "founder_twitter_extraction",
        "description": "extract the twitter information of a founder",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the twitter extraction",
                    "properties": {
                        "twitter_url": {
                            "type": "string",
                            "description": "The twitter url of the founder",
                        },
                        "twitter_info": {
                            "type": "string",
                            "description": "The twitter information of the founder"
                        }

                    }
                },
            },
            "required": ["results"],
        },

    },
    {
        "name": "founder_contact_extraction",
        "description": "extract the contact information of a founder",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the contact extraction",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email address of the founder or company",
                        },
                    }
                },
            },
            "required": ["results"],
        },
    },
{
        "name": "rejection_email",
        "description": "write an empathetic rejection email from an investor",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the contact extraction",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email address of the founder or company",
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the email",
                        },
                        "body": {
                            "type": "string",
                            "description": "The body of the email",
                        }
                    }
                },
            },
            "required": ["results"],
        },
    },
{
        "name": "meeting_email",
        "description": "write an empathetic email from an investor requesting a meeting",
        "parameters": {
            "type": "object",
            "properties": {
                "results": {
                    "type": "object",
                    "description": "the results of the contact extraction",
                    "properties": {
                        "email": {
                            "type": "string",
                            "description": "The email address of the founder or company",
                        },
                        "subject": {
                            "type": "string",
                            "description": "The subject of the email",
                        },
                        "body": {
                            "type": "string",
                            "description": "The body of the email",
                        }
                    }
                },
            },
            "required": ["results"],
        },
    }

]
