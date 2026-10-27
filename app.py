"""
app.py
------
PHASE 6 (FINAL) VERSION.

The full Skilled Sapiens B2B Lead Qualification & Growth Strategy Agent
dashboard. This wires the entire agent pipeline (research -> segmentation
-> scoring -> service matching -> next action -> outreach) into the
7-section dashboard described in the project brief:

  1. Company Information (input form)
  2. Lead Overview (score, priority, segment)
  3. AI Analysis (research findings, if any)
  4. Service Recommendation (with reason, alternative, confidence)
  5. Sales Recommendation (decision maker, next action, channel)
  6. Personalized Outreach (email + LinkedIn message)
  7. Agent Activity (high-level tool log - no raw chain-of-thought)

Run with:  streamlit run app.py
"""

import streamlit as st

import config
from agent import run_agent


# ============================================================
# PAGE SETUP
# ============================================================

st.set_page_config(
    page_title="Skilled Sapiens B2B Lead Agent",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Skilled Sapiens B2B Lead Qualification & Growth Strategy Agent")
st.caption(
    "An agentic AI prototype developed as an extension of a Skilled Sapiens "
    "live strategy project - not an internal Skilled Sapiens system."
)

# --- Configuration check, before anything else runs ---
is_valid, config_message = config.validate_config()
if not is_valid:
    st.error(f"Configuration problem: {config_message}")
    st.info(
        "Fix this by:\n"
        "1. Copy .env.example to a new file named .env\n"
        "2. Open .env and paste in your free Groq API key "
        "(get one at console.groq.com/keys)\n"
        "3. Restart this app"
    )
    st.stop()

# Keep the analysis result across Streamlit re-runs (e.g. when the user
# clicks a button elsewhere on the page) so the report doesn't disappear.
if "report" not in st.session_state:
    st.session_state.report = None


# ============================================================
# SECTION 1: COMPANY INFORMATION (input form)
# ============================================================

st.header("1. Company Information")

with st.form("company_info_form"):
    col1, col2 = st.columns(2)

    with col1:
        company_name = st.text_input("Company Name *", placeholder="e.g. ABC Technologies")
        industry = st.text_input("Industry *", placeholder="e.g. IT, Consulting, Startup, SME")
        employees = st.number_input("Number of Employees *", min_value=0, step=1, value=0)
        location = st.text_input("Location", placeholder="e.g. Bangalore")

    with col2:
        website = st.text_input("Website (optional)", placeholder="e.g. https://example.com")
        growth_info = st.text_area(
            "Growth / Hiring Information",
            placeholder="e.g. Hiring 100 employees, expanding into new markets...",
            height=100,
        )
        business_need = st.text_area(
            "Business / Training Requirement *",
            placeholder="e.g. AI and Digital Transformation upskilling",
            height=100,
        )

    submitted = st.form_submit_button("Analyze Lead", use_container_width=True)

if submitted:
    # Basic client-side validation before even calling the agent -
    # catches empty required fields with a friendly message, rather
    # than letting the agent's own validation handle everything.
    if not company_name.strip() or not industry.strip() or not business_need.strip():
        st.warning("Please fill in all required fields (marked with *) before analyzing.")
    else:
        company_data = {
            "company_name": company_name.strip(),
            "industry": industry.strip(),
            "employees": int(employees) if employees else None,
            "location": location.strip(),
            "website": website.strip() if website else None,
            "growth_info": growth_info.strip(),
            "business_need": business_need.strip(),
        }
        with st.spinner("Agent is analyzing this lead..."):
            st.session_state.report = run_agent(company_data)


# ============================================================
# Everything below only renders once we have a report
# ============================================================

report = st.session_state.report

if report is None:
    st.info("Fill in the company information above and click Analyze Lead to begin.")
    st.stop()

if report["status"] == "incomplete":
    st.error(f"{report['message']}")
    st.caption(
        "The agent will not guess or fabricate a score without enough "
        "information. Please fill in the missing fields above and try again."
    )
    with st.expander("Agent Activity Log"):
        for i, entry in enumerate(report["activity_log"], start=1):
            st.write(f"{i}. {entry}")
    st.stop()


# ============================================================
# SECTION 2: LEAD OVERVIEW
# ============================================================

st.header("2. Lead Overview")

score = report["score"]
segment = report["segment"]

priority_colors = {"HIGH": "green", "MEDIUM": "orange", "LOW": "red"}

col1, col2, col3, col4 = st.columns(4)
col1.metric("Lead Score", f"{score['total_score']}/100")
col2.metric("Priority", score["priority"])
col3.metric("Company Segment", segment["segment_label"])
col4.metric("Business Need", segment["need_category"])

st.progress(score["total_score"] / 100)

with st.expander("See full score breakdown"):
    for factor_name, factor_result in score["breakdown"].items():
        label = factor_name.replace("_", " ").title()
        st.write(
            f"**{label}:** {factor_result['score']}/{factor_result['max_score']} "
            f"- {factor_result['reason']}"
        )


# ============================================================
# SECTION 3: AI ANALYSIS
# ============================================================

st.header("3. AI Analysis")

research = report.get("research")

if research is None:
    st.info(
        "The information provided was specific enough that the agent did not "
        "need to research this company externally. This analysis is based "
        "entirely on the information you entered."
    )
elif research["status"] == "ok":
    st.write("**External research summary (grounded in real web sources):**")
    st.write(research["summary"])
    if research["raw_snippets"]:
        with st.expander(f"See {len(research['raw_snippets'])} source(s) used"):
            for s in research["raw_snippets"]:
                st.markdown(f"- [{s['title']}]({s['url']})")
else:
    st.warning(
        f"External research was attempted but unavailable or found nothing "
        f"useful ({research['status']}). Analysis is based on user-provided "
        "information only - the agent did not fabricate additional findings."
    )


# ============================================================
# SECTION 4: SERVICE RECOMMENDATION
# ============================================================

st.header("4. Service Recommendation")

service = report["service"]

col1, col2 = st.columns([2, 1])
with col1:
    st.subheader(service["recommended_service"])
    st.write(f"**Why this service fits:** {service['reason']}")
    st.write(f"**Alternative option:** {service['alternative_service']}")
with col2:
    st.metric("Confidence", f"{service['confidence']}%")
    st.progress(service["confidence"] / 100)


# ============================================================
# SECTION 5: SALES RECOMMENDATION
# ============================================================

st.header("5. Sales Recommendation")

next_action = report["next_action"]

col1, col2 = st.columns(2)
with col1:
    st.write(f"**Recommended Decision Maker:** {next_action['recommended_decision_maker']}")
    st.write(f"**Recommended Next Action:** {next_action['recommended_action']}")
with col2:
    st.write(f"**Suggested Channel:** {next_action['suggested_channel']}")
    st.write(f"**Follow-up:** {next_action['follow_up_recommendation']}")


# ============================================================
# SECTION 6: PERSONALIZED OUTREACH
# ============================================================

st.header("6. Personalized Outreach")

outreach = report["outreach"]

st.subheader("Email")
st.text_input("Subject line", value=outreach["email_subject"], key="outreach_subject")
st.text_area("Email body", value=outreach["email_body"], height=180, key="outreach_email")

st.subheader("LinkedIn Message")
st.text_area("LinkedIn message", value=outreach["linkedin_message"], height=100, key="outreach_linkedin")

st.caption(
    "Click into any box above and use Ctrl+A, Ctrl+C to copy the text "
    "(Streamlit doesn't support one-click copy buttons in this version)."
)


# ============================================================
# SECTION 7: AGENT ACTIVITY
# ============================================================

st.header("7. Agent Activity")
st.caption("A high-level trail of what the agent did and why - not its internal reasoning.")

for i, entry in enumerate(report["activity_log"], start=1):
    st.write(f"{i}. {entry}")
