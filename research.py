"""
research.py
-----------
TOOL 1 from the project brief: Company Research.

Uses Tavily's free web search API to look up real, external information
about a company - recent news, hiring signals, growth activity, digital
transformation / AI adoption signals.

CRITICAL RULE (per the project brief): never fabricate company
information. If no search API key is configured, the search fails, or
nothing useful is found, this tool says so clearly. It does NOT invent
details to fill the gap - the agent then simply relies on whatever the
user typed in themselves.

Design note: the search provider is isolated to this one file. If you
wanted to swap Tavily for another provider later, only this file (and
config.py) would need to change - nothing else in the project depends
on Tavily directly.
"""

import config
import prompts
from openai import OpenAI

try:
    from tavily import TavilyClient
    TAVILY_SDK_INSTALLED = True
except ImportError:
    # If the package somehow isn't installed, we degrade gracefully
    # instead of crashing the whole app.
    TAVILY_SDK_INSTALLED = False


def is_research_available() -> bool:
    """Checks whether external web research can even be attempted."""
    return TAVILY_SDK_INSTALLED and bool(config.TAVILY_API_KEY)


def search_company(company_name: str, website: str = None) -> dict:
    """
    Attempts to search the web for information about a company.

    Returns a dict:
        status: "ok" | "unavailable" | "no_results" | "error"
        message: human-readable explanation of what happened
        raw_snippets: list of {title, url, content} - only populated if status == "ok"

    This function is intentionally "dumb" - it just fetches raw search
    results. Turning those into a clean summary happens separately in
    summarize_research(), so each step can be tested/debugged on its own.
    """
    if not is_research_available():
        return {
            "status": "unavailable",
            "message": (
                "External research unavailable (no TAVILY_API_KEY configured). "
                "Falling back to user-provided information only."
            ),
            "raw_snippets": [],
        }

    query = company_name
    if website:
        query += f" ({website})"
    query += " company hiring growth digital transformation AI adoption news"

    try:
        client = TavilyClient(api_key=config.TAVILY_API_KEY)
        response = client.search(query=query, max_results=4, search_depth="basic")
        results = response.get("results", [])

        if not results:
            return {
                "status": "no_results",
                "message": f"No external web results found for '{company_name}'.",
                "raw_snippets": [],
            }

        # Keep snippets short - we only need enough for the LLM to
        # summarize, not full article text.
        snippets = [
            {
                "title": r.get("title", "Untitled"),
                "url": r.get("url", ""),
                "content": (r.get("content", "") or "")[:500],
            }
            for r in results
        ]

        return {
            "status": "ok",
            "message": f"Found {len(snippets)} external result(s) for '{company_name}'.",
            "raw_snippets": snippets,
        }

    except Exception as e:
        # Network errors, invalid API key, rate limits, etc. all land here.
        # We fail gracefully rather than crashing the agent.
        return {
            "status": "error",
            "message": f"Web research failed ({e}). Falling back to user-provided information only.",
            "raw_snippets": [],
        }


def summarize_research(company_name: str, search_result: dict) -> str:
    """
    Turns raw search snippets into a short, grounded summary using the LLM.

    If search_result's status isn't "ok" (unavailable, no_results, or
    error), we do NOT call the LLM at all - there's nothing to summarize,
    and calling it anyway risks the LLM filling gaps with invented facts.
    """
    if search_result["status"] != "ok" or not search_result["raw_snippets"]:
        return search_result["message"]  # just pass through the honest status message

    snippets_text = "\n\n".join(
        f"[{s['title']}]({s['url']})\n{s['content']}" for s in search_result["raw_snippets"]
    )

    try:
        client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompts.RESEARCH_SUMMARY_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompts.RESEARCH_SUMMARY_USER_TEMPLATE.format(
                        company_name=company_name, snippets=snippets_text
                    ),
                },
            ],
            max_tokens=250,
            temperature=0.3,
        )
        return response.choices[0].message.content

    except Exception as e:
        return (
            f"Could not summarize research due to an LLM error ({e}). "
            f"Raw search found {len(search_result['raw_snippets'])} result(s) - "
            "see raw_snippets for details."
        )


def research_company(company_name: str, website: str = None) -> dict:
    """
    Main entry point for this file. Combines search + summarization into
    one call, returning everything the agent needs.
    """
    search_result = search_company(company_name, website)
    summary = summarize_research(company_name, search_result)

    return {
        "status": search_result["status"],
        "summary": summary,
        "raw_snippets": search_result["raw_snippets"],
    }
