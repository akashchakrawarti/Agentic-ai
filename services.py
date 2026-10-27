"""
services.py
-----------
TOOL 4 from the project brief: Service Recommendation.

Matches a segmented company (industry, size, business need) to the most
suitable Skilled Sapiens service, following the mapping rules given in
the project brief. Also returns a reason, an alternative service, and a
confidence score - so the recommendation is never a black box.
"""

# --- Service definitions (also mirrored in data/services.json for the RAG step later) ---
SERVICES = {
    "Corporate Capability Labs": {
        "target": "Mid-level managers, corporate teams",
        "focus": "Leadership, design thinking, data storytelling, managerial capability development",
        "decision_maker": "L&D Head / HR Head / CHRO",
    },
    "Startup Acceleration Program": {
        "target": "Startups, entrepreneurs",
        "focus": "Market validation, GTM strategy, investor readiness, business strategy, mentorship",
        "decision_maker": "Founder / CEO",
    },
    "Industry-Curated Learning Pods": {
        "target": "SMEs, corporates, IT companies",
        "focus": "AI, digital transformation, emerging tech, workforce upskilling",
        "decision_maker": "HR Head / L&D Head / CHRO",
    },
    "Fractional Consulting": {
        "target": "Startups, SMEs",
        "focus": "Strategy, HR, sales, product, finance consulting",
        "decision_maker": "Founder / CEO / Functional Head",
    },
}


def match_service(segment: dict) -> dict:
    """
    Applies the mapping rules from the project brief to pick the best
    service, an alternative, and a confidence score (0-100).

    segment must contain: industry_category, size_category, need_category
    (this is exactly the dict returned by segmentation.segment_company()).
    """
    industry = segment["industry_category"]
    size = segment["size_category"]
    need = segment["need_category"]

    # --- Rule 1: Startup + GTM/investor readiness need -> Startup Acceleration ---
    if industry == "Startup" and need == "Startup Growth":
        return {
            "recommended_service": "Startup Acceleration Program",
            "reason": (
                "The company is an early-stage startup with a stated need around "
                "go-to-market strategy or investor readiness, which is exactly what "
                "the Startup Acceleration Program is designed for."
            ),
            "alternative_service": "Fractional Consulting",
            "confidence": 90,
        }

    # --- Rule 2: Leadership/managerial need + larger company -> Corporate Capability Labs ---
    if need == "Leadership Development" and size in ("Large", "Medium"):
        return {
            "recommended_service": "Corporate Capability Labs",
            "reason": (
                "The company has a clear leadership/managerial development need and "
                "sufficient scale (Medium/Large) to justify a structured capability-building "
                "program for its management layer."
            ),
            "alternative_service": "Industry-Curated Learning Pods",
            "confidence": 85,
        }

    # --- Rule 3: AI/Digital transformation need -> Industry-Curated Learning Pods ---
    if need in ("AI Upskilling", "Digital Transformation"):
        return {
            "recommended_service": "Industry-Curated Learning Pods",
            "reason": (
                f"The company has a specific requirement around {need.lower()}, which "
                "directly matches the focus of the Industry-Curated Learning Pods "
                "(AI, digital transformation, emerging technologies)."
            ),
            "alternative_service": "Corporate Capability Labs",
            "confidence": 88,
        }

    # --- Rule 4: Startup/SME + strategy/HR/sales/product/finance -> Fractional Consulting ---
    if industry in ("Startup", "SME") and need in ("Strategy", "HR", "Sales", "Product", "Finance"):
        return {
            "recommended_service": "Fractional Consulting",
            "reason": (
                f"As a {industry.lower()}, the company likely cannot justify a full-time "
                f"{need.lower()} hire yet, but has a real need in this area - a strong fit "
                "for Fractional Consulting."
            ),
            "alternative_service": "Startup Acceleration Program" if industry == "Startup" else "Industry-Curated Learning Pods",
            "confidence": 80,
        }

    # --- Fallback: no strong rule matched - lower confidence, best-guess service ---
    if size in ("Large", "Medium"):
        fallback_service = "Industry-Curated Learning Pods"
    else:
        fallback_service = "Fractional Consulting"

    return {
        "recommended_service": fallback_service,
        "reason": (
            "No single strong rule matched this company's profile precisely. "
            f"Based on its size ({size}) and general profile, {fallback_service} is "
            "the most reasonable starting point, but this should be verified during "
            "a discovery call."
        ),
        "alternative_service": "Corporate Capability Labs" if fallback_service != "Corporate Capability Labs" else "Fractional Consulting",
        "confidence": 55,
    }
