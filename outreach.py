"""
outreach.py
-----------
TOOL 6 from the project brief: Personalized Outreach Generator.

Generates a professional B2B outreach package - email subject, email
body, and a short LinkedIn message - personalized using the company's
actual profile, not a generic template.

Grounding rule: the LLM only receives real facts we already established
(from segmentation, scoring, service matching, and optionally external
research) and is explicitly instructed not to invent anything beyond
that - no fabricated achievements, funding news, or statistics.
"""

from openai import OpenAI

import config
import prompts


def _build_context_summary(report: dict) -> str:
    """
    Turns the agent's report into a plain-text context block for the
    outreach prompt. Kept separate from the LLM call so it's easy to
    inspect exactly what facts an outreach message is grounded in.
    """
    segment = report["segment"]
    service = report["service"]

    lines = [
        f"Company name: {report['company_name']}",
        f"Industry: {segment['industry_category']}",
        f"Company size category: {segment['size_category']}",
        f"Business need identified: {segment['need_category']}",
        f"Recommended Skilled Sapiens service: {service['recommended_service']}",
        f"Reason this service fits: {service['reason']}",
    ]

    # Only include external research if it actually succeeded - never
    # let the prompt imply there's research backing when there isn't.
    research = report.get("research")
    if research and research.get("status") == "ok":
        lines.append(f"External research findings: {research['summary']}")

    return "\n".join(lines)


def _parse_outreach_response(raw_text: str) -> dict:
    """
    Parses the LLM's delimited response (SUBJECT: / EMAIL: / LINKEDIN:)
    into three separate fields. Plain delimiters are used instead of
    JSON since they're easier to debug and more forgiving of small
    formatting differences from the LLM.
    """
    result = {"email_subject": "", "email_body": "", "linkedin_message": ""}
    current_key = None
    buffer = []

    def flush():
        if current_key:
            result[current_key] = "\n".join(buffer).strip()

    for line in raw_text.splitlines():
        stripped = line.strip()
        if stripped.upper().startswith("SUBJECT:"):
            flush()
            current_key = "email_subject"
            buffer = [stripped[len("SUBJECT:"):].strip()]
        elif stripped.upper().startswith("EMAIL:"):
            flush()
            current_key = "email_body"
            buffer = [stripped[len("EMAIL:"):].strip()]
        elif stripped.upper().startswith("LINKEDIN:"):
            flush()
            current_key = "linkedin_message"
            buffer = [stripped[len("LINKEDIN:"):].strip()]
        elif current_key:
            buffer.append(line)
    flush()

    # If the LLM didn't follow the format at all, don't lose the output -
    # dump it into email_body rather than returning empty fields.
    if not any(result.values()):
        result["email_body"] = raw_text

    return result


def generate_outreach(report: dict) -> dict:
    """
    Generates outreach content for a company that has already been
    through segmentation, scoring, and service matching.

    Returns: {"email_subject": str, "email_body": str, "linkedin_message": str}
    On failure, returns a safe fallback so the UI never breaks.
    """
    context_summary = _build_context_summary(report)

    try:
        client = OpenAI(api_key=config.GROQ_API_KEY, base_url=config.GROQ_BASE_URL)
        response = client.chat.completions.create(
            model=config.LLM_MODEL,
            messages=[
                {"role": "system", "content": prompts.OUTREACH_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": prompts.OUTREACH_USER_TEMPLATE.format(context=context_summary),
                },
            ],
            max_tokens=500,
            temperature=0.6,  # slightly more creative than RAG/research - this is persuasive writing
        )
        raw_text = response.choices[0].message.content
        return _parse_outreach_response(raw_text)

    except Exception as e:
        fallback_msg = f"Could not generate outreach due to an LLM error: {e}"
        return {
            "email_subject": "(unavailable)",
            "email_body": fallback_msg,
            "linkedin_message": fallback_msg,
        }
