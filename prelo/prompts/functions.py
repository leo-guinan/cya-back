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
                                    "description": "The reasoning behind the score"
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
                                    "description": "The reasoning behind the score"
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
                                    "description": "The reasoning behind the score"
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
                                    "description": "The reasoning behind the score"
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
]
