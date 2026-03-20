from src.schemas.universities import UniversitySearchArgs

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_universities",
            "description": "Search the local database for Pakistani universities matching specific criteria. Use this tool whenever a student asks about universities, programs, locations, or fees. This is your primary source of accurate university information.",
            "parameters": UniversitySearchArgs.model_json_schema(),
        },
    },
    {
        "type": "function",
        "function": {
            "name": "brave_search",
            "description": "Search the web for general information when specific university data is not available. Use this as a fallback to find additional context or information not in the local database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find on the web",
                    },
                    "count": {
                        "type": "integer",
                        "description": "Number of results to return (1-10, default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]
