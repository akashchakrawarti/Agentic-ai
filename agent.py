"""
agent.py
--------
The agent orchestrator.

GOAL (as stated in the project brief):
    "Qualify and prioritize a potential B2B client for Skilled Sapiens."

This is what makes the project "agentic" rather than just a script:
the agent looks at the situation and DECIDES what to do next, instead of
always running the same fixed sequence blindly.

Specifically, the agent:
  1. Validates the input first. If critical information is missing, it
     stops and reports exactly what's missing - it does NOT guess or
     fabricate values to keep going.
  2. Only if validation passes, it runs the tool pipeline:
     segmentation -> lead scoring -> service matching -> next best action.
  3. Logs each step at a high level (tool name + one-line result) so the
     UI can later show an "Agent Activity" trail, without exposing any
     internal reasoning/chain-of-thought.
  4. Returns one structured report - this is the single object the
     Streamlit UI will read from in Phase 6.
"""

from segmentation import segment_company
from scoring import calculate_lead_score
from services import match_service, SERVICES
from research import research_company, is_research_available
from outreach import generate_outreach


# --- Fields the agent considers essential before it will proceed ---
# This encodes the agent's "decision policy": what does it need to know
# before it can responsibly qualify a lead?
REQUIRED_FIELDS = ["company_name", "industry", "employees", "business_need"]

# Values that count as "no real information provided" for a free-text
# field - used by needs_research() below to decide if the input is too
# thin to qualify a lead confidently without external help.
THIN_VALUES = {"", "not specified", "unknown", "n/a", "na", "none", "tbd"}


def needs_research(company_data: dict) -> bool:
    """
    Part of the agent's decision policy: decides whether external web
    research would meaningfully help, based on how much useful detail
    the user actually provided.

    Research is considered useful when growth/hiring info is missing,
    OR the stated business need is vague/unspecified - in both cases,
    external signals could fill a real gap. If the user already gave
    clear, specific information, we skip research to save time/API calls.
    """
    growth_text = (company_data.get("growth_info") or "").strip().lower()
    need_text = (company_data.get("business_need") or "").strip().lower()

    if growth_text in THIN_VALUES:
        return True
    if need_text in THIN_VALUES:
        return True
    return False


def validate_input(company_data: dict) -> dict:
    """
    Step 1 of the agent's decision policy: check whether there's enough
    information to proceed.

    Returns a dict: {"is_valid": bool, "missing_fields": [...], "message": str}
    """
    missing_fields = []

    for field in REQUIRED_FIELDS:
        value = company_data.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing_fields.append(field)

    # Employees must be a usable number if provided
    employees = company_data.get("employees")
    if employees is not None:
        try:
            int(employees)
        except (ValueError, TypeError):
            missing_fields.append("employees (must be a valid number)")

    if missing_fields:
        return {
            "is_valid": False,
            "missing_fields": missing_fields,
            "message": (
                "Cannot qualify this lead yet - missing or invalid: "
                + ", ".join(missing_fields)
            ),
        }

    return {"is_valid": True, "missing_fields": [], "message": "Input is complete."}


def determine_next_action(score_result: dict, segment: dict, service_result: dict) -> dict:
    """
    TOOL 5 from the brief: Next Best Action.

    Deterministic rules based on priority + business need - not an LLM
    guess. This mirrors how a real sales-ops playbook would work.
    """
    priority = score_result["priority"]
    decision_maker = SERVICES[service_result["recommended_service"]]["decision_maker"]

    if priority == "HIGH":
        action = "Schedule a discovery call"
        channel = "Email + LinkedIn (direct outreach)"
        follow_up = "Follow up within 2 business days if no response"
    elif priority == "MEDIUM":
        action = "Send a personalized email and conduct a needs assessment"
        channel = "Email, with LinkedIn as backup"
        follow_up = "Follow up within 5-7 business days"
    else:  # LOW
        action = "Add to nurture sequence; do not prioritize active outreach yet"
        channel = "LinkedIn (light-touch content engagement)"
        follow_up = "Revisit in 60-90 days or if new growth signals appear"

    return {
        "recommended_action": action,
        "recommended_decision_maker": decision_maker,
        "suggested_channel": channel,
        "follow_up_recommendation": follow_up,
    }


def run_agent(company_data: dict) -> dict:
    """
    Main entry point. Runs the full agent workflow on a single company's
    raw input data and returns one structured report.

    company_data expected keys:
        company_name, industry, employees, location (optional),
        growth_info (optional), business_need, website (optional)

    Returns a dict with keys:
        status ("ok" or "incomplete"), activity_log, and - if status is
        "ok" - segment, score, service, next_action.
    """
    activity_log = []

    # --- Step 1: Validate input ---
    validation = validate_input(company_data)
    if not validation["is_valid"]:
        activity_log.append(f"Input validation failed: {validation['message']}")
        return {
            "status": "incomplete",
            "message": validation["message"],
            "missing_fields": validation["missing_fields"],
            "activity_log": activity_log,
        }
    activity_log.append("Input validated - all required fields present")

    # --- Step 2: Decide whether additional research is needed ---
    # This is a real agentic decision - the agent looks at what it already
    # knows and only spends a web search call when the input is genuinely
    # thin. Lead scoring itself always stays based on user-provided data
    # (kept deterministic per the project brief) - research is used to
    # add context and personalize the outreach message, not to change the score.
    research_result = None
    if needs_research(company_data):
        if is_research_available():
            activity_log.append(
                "Growth/need information is thin - researching company externally"
            )
            research_result = research_company(
                company_data["company_name"], company_data.get("website")
            )
            activity_log.append(f"Research completed -> status: {research_result['status']}")
        else:
            activity_log.append(
                "Growth/need information is thin, but external research is unavailable "
                "(no Tavily key configured) - proceeding with user-provided information only"
            )
    else:
        activity_log.append("Sufficient information provided - skipping external research")

    # --- Step 3: Segmentation ---
    segment = segment_company(
        industry_text=company_data["industry"],
        employee_count=int(company_data["employees"]),
        need_text=company_data["business_need"],
    )
    activity_log.append(
        f"Segmentation completed -> {segment['segment_label']} "
        f"(need: {segment['need_category']})"
    )

    # --- Step 4: Lead Scoring ---
    growth_text = company_data.get("growth_info", "")
    score_result = calculate_lead_score(segment, growth_text)
    activity_log.append(
        f"Lead scored -> {score_result['total_score']}/100 "
        f"({score_result['priority']} priority)"
    )

    # --- Step 5: Service Matching ---
    service_result = match_service(segment)
    activity_log.append(
        f"Service matched -> {service_result['recommended_service']} "
        f"(confidence: {service_result['confidence']}%)"
    )

    # --- Step 6: Next Best Action ---
    next_action = determine_next_action(score_result, segment, service_result)
    activity_log.append(f"Next action determined -> {next_action['recommended_action']}")

    report = {
        "status": "ok",
        "company_name": company_data["company_name"],
        "segment": segment,
        "score": score_result,
        "service": service_result,
        "next_action": next_action,
        "research": research_result,
        "activity_log": activity_log,
    }

    # --- Step 7: Personalized Outreach Generation ---
    outreach_result = generate_outreach(report)
    activity_log.append("Personalized outreach generated")
    report["outreach"] = outreach_result

    return report
