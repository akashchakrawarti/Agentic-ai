"""
segmentation.py
----------------
TOOL 2 from the project brief: Customer Segmentation.

Takes the raw info a user types in (industry, employee count, stated need)
and turns it into clean, standardized categories we can use for scoring
and service matching later.

This is plain Python logic - no AI involved. Deterministic and explainable,
which matters for an interview ("how does the agent decide this?").
"""

import config


# --- Reference lists used to classify free-text industry input ---
# Keeping these as simple lists (not a complex NLP model) is intentional -
# it's transparent, and easy to extend later.

IT_KEYWORDS = ["it", "software", "tech", "information technology", "saas"]
CONSULTING_KEYWORDS = ["consulting", "advisory"]
EDTECH_KEYWORDS = ["edtech", "education technology"]
STARTUP_KEYWORDS = ["startup"]
EDUCATION_KEYWORDS = ["university", "college", "school", "education", "institution"]
SME_KEYWORDS = ["sme", "small business", "manufacturing", "retail", "logistics"]

# Business need classification keywords.
# We check the user's free-text "requirement" field against these.
NEED_KEYWORDS = {
    "AI Upskilling": ["ai", "artificial intelligence", "machine learning", "genai", "gen ai"],
    "Digital Transformation": ["digital transformation", "digitization", "digitalization", "automation"],
    "Leadership Development": ["leadership", "management", "managerial", "people management"],
    "Startup Growth": ["gtm", "go-to-market", "go to market", "investor readiness", "fundraising", "market validation"],
    "Strategy": ["strategy", "strategic planning", "business strategy"],
    "HR": ["hr", "human resources", "talent", "recruitment"],
    "Sales": ["sales", "business development"],
    "Product": ["product", "product management"],
    "Finance": ["finance", "financial planning"],
    "Employability": ["employability", "career readiness", "job readiness"],
}


def classify_industry(industry_text: str) -> str:
    """
    Classifies a free-text industry string into a standard category.
    Returns one of: IT, Consulting, EdTech, Startup, SME, Education, Other
    """
    if not industry_text:
        return "Other"

    text = industry_text.lower().strip()

    if any(kw in text for kw in IT_KEYWORDS):
        return "IT"
    if any(kw in text for kw in CONSULTING_KEYWORDS):
        return "Consulting"
    if any(kw in text for kw in EDTECH_KEYWORDS):
        return "EdTech"
    if any(kw in text for kw in STARTUP_KEYWORDS):
        return "Startup"
    if any(kw in text for kw in EDUCATION_KEYWORDS):
        return "Education"
    if any(kw in text for kw in SME_KEYWORDS):
        return "SME"

    return "Other"


def classify_company_size(employee_count: int) -> str:
    """
    Classifies company size using the configurable bands in config.py.
    Returns: Small, Medium, or Large
    """
    if employee_count is None:
        return "Unknown"

    if employee_count <= config.COMPANY_SIZE_BANDS["SMALL_MAX"]:
        return "Small"
    elif employee_count <= config.COMPANY_SIZE_BANDS["MEDIUM_MAX"]:
        return "Medium"
    else:
        return "Large"


def classify_business_need(need_text: str) -> str:
    """
    Classifies the free-text business/training requirement into a category.
    Returns one of the keys in NEED_KEYWORDS, or "Other" if nothing matches.
    """
    if not need_text:
        return "Other"

    text = need_text.lower().strip()

    for category, keywords in NEED_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return category

    return "Other"


def build_company_segment_label(industry_category: str, size_category: str) -> str:
    """
    Combines industry + size into a single human-readable segment label,
    e.g. "IT SME", "Startup Small", "Corporate Large".
    This matches the "Company Segment" field shown in your example output.
    """
    # "Corporate" is used instead of the raw industry when the company is Large,
    # matching typical B2B segmentation language.
    if size_category == "Large":
        return f"Corporate {industry_category}"
    elif size_category == "Small" and industry_category in ("Startup", "SME"):
        return f"{industry_category}"
    else:
        return f"{industry_category} {size_category}"


def segment_company(industry_text: str, employee_count: int, need_text: str) -> dict:
    """
    Main entry point for this file. Runs all three classifications and
    returns a single structured dictionary - this is what other files
    (scoring.py, services.py, app.py) will import and use.
    """
    industry_category = classify_industry(industry_text)
    size_category = classify_company_size(employee_count)
    need_category = classify_business_need(need_text)
    segment_label = build_company_segment_label(industry_category, size_category)

    return {
        "industry_category": industry_category,
        "size_category": size_category,
        "need_category": need_category,
        "segment_label": segment_label,
    }
