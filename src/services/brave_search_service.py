import logging

import requests

from src.config import settings

logger = logging.getLogger(__name__)


def brave_search(query: str, count: int = 5) -> list[dict]:
    """
    Search the web using Brave Search API.

    Args:
        query: The search query string
        count: Number of results to return (default: 5)

    Returns:
        List of search results with title, url, and description
    """
    if not settings.BRAVE_SEARCH_API_KEY:
        logger.warning("Brave Search API key not configured, returning empty results")
        return []

    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": settings.BRAVE_SEARCH_API_KEY,
        }
        params = {
            "q": query,
            "count": count,
        }

        response = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers=headers,
            params=params,
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        results = []

        # Extract web results
        if "web" in data:
            for result in data["web"].get("results", [])[:count]:
                results.append(
                    {
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "description": result.get("description", ""),
                    }
                )

        logger.info(f"Brave Search found {len(results)} results for query: {query}")
        return results

    except requests.exceptions.RequestException as e:
        logger.error(f"Brave Search API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in brave_search: {e}")
        return []
