"""
test_integration.py
--------------------
Runs the FULL agent pipeline - including the research decision and
outreach generation added in this step - on two sample companies:

  1. ABC Technologies: has complete growth/need info -> agent should
     SKIP research (input isn't thin) and go straight to scoring.
  2. A deliberately thin-info company -> agent should DECIDE to research
     it (if a Tavily key is configured) before proceeding.

Run with:  python test_integration.py
"""

from agent import run_agent


def print_full_report(report: dict):
    print("\nAGENT ACTIVITY LOG:")
    for i, entry in enumerate(report["activity_log"], start=1):
        print(f"  {i}. {entry}")

    if report["status"] == "incomplete":
        print(f"\nRESULT: INCOMPLETE - {report['message']}")
        return

    print(f"\nCOMPANY: {report['company_name']}")
    print(f"Segment: {report['segment']['segment_label']}")
    print(f"Lead Score: {report['score']['total_score']}/100 -> {report['score']['priority']} priority")
    print(f"Recommended Service: {report['service']['recommended_service']}")

    if report.get("research"):
        print(f"\nResearch status: {report['research']['status']}")
        print(f"Research summary: {report['research']['summary']}")

    outreach = report["outreach"]
    print(f"\nEmail Subject: {outreach['email_subject']}")
    print(f"\nEmail Body:\n{outreach['email_body']}")
    print(f"\nLinkedIn Message:\n{outreach['linkedin_message']}")


def main():
    print("=" * 70)
    print("CASE 1: Complete information (should SKIP research)")
    print("=" * 70)
    complete_company = {
        "company_name": "ABC Technologies",
        "industry": "IT",
        "employees": 500,
        "location": "Bangalore",
        "growth_info": "Hiring 100 employees",
        "business_need": "AI and Digital Transformation upskilling",
    }
    report1 = run_agent(complete_company)
    print_full_report(report1)

    print("\n\n" + "=" * 70)
    print("CASE 2: Thin information (agent should DECIDE research is needed)")
    print("=" * 70)
    thin_company = {
        "company_name": "Infosys",
        "industry": "IT",
        "employees": 300000,
        "location": "Bangalore",
        "growth_info": "Not specified",
        "business_need": "Not specified",
    }
    report2 = run_agent(thin_company)
    print_full_report(report2)


if __name__ == "__main__":
    main()
