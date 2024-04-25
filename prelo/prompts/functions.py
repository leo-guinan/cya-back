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
                        "founders": {
                            "type": "string",
                            "description": "The founders and/or team"
                        },
                        "industy": {
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

                    }
                },
            },
            "required": ["results"],
        },
    },
]