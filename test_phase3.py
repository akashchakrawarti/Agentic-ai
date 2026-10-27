"""
test_phase3.py
---------------
Runs the full agent (agent.run_agent) against all sample companies,
including the deliberately incomplete one - this is Test Case 5 from
the project brief: the agent should report missing info, never hallucinate.

Run with:  python test_phase3.py
"""

import json

from agent import run_agent


def print_report(report: dict):
    print("\nAGENT ACTIVITY LOG:")
    for i, entry in enumerate(report["activity_log"], start=1):
        print(f"  {i}. {entry}")

    if report["status"] == "incomplete":
        print(f"\nRESULT: INCOMPLETE - {report['message']}")
        print(f"Missing fields: {', '.join(report['missing_fields'])}")
        return

    print(f"\nCOMPANY: {report['company_name']}")
    print(f"Segment: {report['segment']['segment_label']}")
    print(f"Lead Score: {report['score']['total_score']}/100 -> {report['score']['priority']} priority")
    print(f"Recommended Service: {report['service']['recommended_service']} "
          f"({report['service']['confidence']}% confidence)")
    print(f"Next Action: {report['next_action']['recommended_action']}")
    print(f"Decision Maker: {report['next_action']['recommended_decision_maker']}")
    print(f"Channel: {report['next_action']['suggested_channel']}")
    print(f"Follow-up: {report['next_action']['follow_up_recommendation']}")


def main():
    with open("data/sample_leads.json", "r", encoding="utf-8") as f:
        leads = json.load(f)

    for lead in leads:
        print("=" * 70)
        print(f"RUNNING AGENT ON: {lead['company_name']}")
        print("=" * 70)
        report = run_agent(lead)
        print_report(report)
        print()


if __name__ == "__main__":
    main()
