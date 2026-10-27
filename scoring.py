"""
scoring.py
----------
TOOL 3 from the project brief: Lead Scoring.

Implements a transparent, deterministic 100-point scoring framework:

    Factor                          Weight
    ------------------------------  ------
    Training/Business Need             30
    Company Size                       20
    Growth/Hiring                      20
    Industry Fit                       15
    Budget/Commercial Potential        15
    ------------------------------  ------
    Total                              100

Every factor is calculated with plain if/else rules, so the score can
always be explained ("why did this company get 87?") - this is important
both for a real sales team trusting the tool, and for your interview.
"""

import config


# --- Factor 1: Training / Business Need (max 30) ---
def score_business_need(need_category: str) -> dict:
    """
    A clearly identified, specific need scores highest.
    An unclear/"Other" need scores lowest, since it's harder to sell into.
    """
    max_score = 30

    if need_category != "Other":
        score = 30  # Specific, matchable need identified
        reason = f"Clear business need identified: {need_category}"
    else:
        score = 10  # Some interest exists, but unclear what to sell
        reason = "No specific business need identified from input"

    return {"score": score, "max_score": max_score, "reason": reason}


# --- Factor 2: Company Size (max 20) ---
def score_company_size(size_category: str) -> dict:
    """
    Larger companies generally mean bigger training budgets and more
    seats/users for Skilled Sapiens programs - so size scores are weighted
    toward Medium/Large. This is a configurable business assumption.
    """
    max_score = 20

    size_scores = {
        "Large": 20,
        "Medium": 14,
        "Small": 8,
        "Unknown": 5,
    }
    score = size_scores.get(size_category, 5)
    reason = f"Company size category: {size_category}"

    return {"score": score, "max_score": max_score, "reason": reason}


# --- Factor 3: Growth / Hiring Signal (max 20) ---
GROWTH_KEYWORDS_STRONG = ["hiring", "expanding", "expansion", "scaling", "growth", "growing"]
GROWTH_KEYWORDS_NONE = ["no growth", "not hiring", "downsizing", "layoffs", "freeze"]


def score_growth_signal(growth_text: str) -> dict:
    """
    Looks for hiring/expansion language in the free-text growth field.
    Active hiring = strong buying signal for upskilling/training services.
    """
    max_score = 20

    if not growth_text:
        return {"score": 5, "max_score": max_score, "reason": "No growth/hiring information provided"}

    text = growth_text.lower()

    if any(kw in text for kw in GROWTH_KEYWORDS_NONE):
        return {"score": 0, "max_score": max_score, "reason": "Signals of no growth or downsizing"}

    if any(kw in text for kw in GROWTH_KEYWORDS_STRONG):
        # Check if a number is mentioned (e.g. "hiring 100 employees") -
        # bigger stated hiring numbers get a small bonus, capped at max_score.
        import re
        numbers = re.findall(r"\d+", text)
        if numbers and int(numbers[0]) >= 50:
            return {"score": 20, "max_score": max_score, "reason": f"Strong active hiring signal ({numbers[0]}+ roles)"}
        else:
            return {"score": 14, "max_score": max_score, "reason": "Active hiring/growth signal detected"}

    # Growth text was provided but doesn't match known keywords
    return {"score": 8, "max_score": max_score, "reason": "Growth information provided but unclear signal strength"}


# --- Factor 4: Industry Fit (max 15) ---
def score_industry_fit(industry_category: str) -> dict:
    """
    How well does this industry match Skilled Sapiens' core target
    industries (per your project's customer segmentation work)?
    """
    max_score = 15

    strong_fit = ["IT", "Consulting", "EdTech", "Startup", "SME"]
    moderate_fit = ["Education"]

    if industry_category in strong_fit:
        return {"score": 15, "max_score": max_score, "reason": f"{industry_category} is a core target industry"}
    elif industry_category in moderate_fit:
        return {"score": 10, "max_score": max_score, "reason": f"{industry_category} is a secondary target industry"}
    else:
        return {"score": 5, "max_score": max_score, "reason": "Industry not a primary target segment"}


# --- Factor 5: Budget / Commercial Potential (max 15) ---
def score_budget_potential(size_category: str, industry_category: str) -> dict:
    """
    Proxy for commercial potential, based on company size and industry.
    (In a real deployment, this could pull in funding data, revenue
    estimates, etc. via the research tool - kept simple here.)
    """
    max_score = 15

    if size_category == "Large":
        score = 15
    elif size_category == "Medium":
        score = 10
    elif size_category == "Small" and industry_category == "Startup":
        # Startups often have funding even at small headcount
        score = 8
    else:
        score = 5

    reason = f"Estimated from company size ({size_category}) and industry ({industry_category})"
    return {"score": score, "max_score": max_score, "reason": reason}


def get_priority(total_score: int) -> str:
    """
    Converts the total score into a priority label using the
    configurable thresholds in config.py.
    """
    if total_score >= config.PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif total_score >= config.PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    else:
        return "LOW"


def calculate_lead_score(segment: dict, growth_text: str) -> dict:
    """
    Main entry point. Takes the segmentation result (from segmentation.py)
    plus the raw growth/hiring text, and returns the full scoring breakdown.
    """
    need_result = score_business_need(segment["need_category"])
    size_result = score_company_size(segment["size_category"])
    growth_result = score_growth_signal(growth_text)
    industry_result = score_industry_fit(segment["industry_category"])
    budget_result = score_budget_potential(segment["size_category"], segment["industry_category"])

    total_score = (
        need_result["score"]
        + size_result["score"]
        + growth_result["score"]
        + industry_result["score"]
        + budget_result["score"]
    )

    priority = get_priority(total_score)

    return {
        "total_score": total_score,
        "max_possible": 100,
        "priority": priority,
        "breakdown": {
            "business_need": need_result,
            "company_size": size_result,
            "growth_hiring": growth_result,
            "industry_fit": industry_result,
            "budget_potential": budget_result,
        },
    }
