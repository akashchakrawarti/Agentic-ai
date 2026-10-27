"""
test_phase2.py
---------------
Runs the Phase 2 business logic (segmentation -> scoring -> service
matching) against the 5 sample companies in data/sample_leads.json.

No Streamlit, no LLM calls - just pure Python logic, so we can verify
it's correct before wiring it into the UI.

Run with:  python test_phase2.py
"""

import json

from segmentation import segment_company
from scoring import calculate_lead_score
from services import match_service


def run_company(lead: dict):
    print("=" * 70)
    print(f"COMPANY: {lead['company_name']}")
    print("=" * 70)

    # Step 1: Segmentation
    segment = segment_company(
        industry_text=lead["industry"],
        employee_count=lead["employees"],
        need_text=lead["business_need"],
    )
    print(f"Segment Label     : {segment['segment_label']}")
    print(f"Industry Category : {segment['industry_category']}")
    print(f"Size Category     : {segment['size_category']}")
    print(f"Need Category     : {segment['need_category']}")

    # Step 2: Lead Scoring
    score_result = calculate_lead_score(segment, lead["growth_info"])
    print(f"\nLEAD SCORE: {score_result['total_score']}/{score_result['max_possible']}  "
          f"-> Priority: {score_result['priority']}")
    print("Score Breakdown:")
    for factor_name, factor_result in score_result["breakdown"].items():
        print(f"  - {factor_name:18s}: {factor_result['score']:>2}/{factor_result['max_score']:<3} "
              f"({factor_result['reason']})")

    # Step 3: Service Matching
    service_result = match_service(segment)
    print(f"\nRECOMMENDED SERVICE: {service_result['recommended_service']} "
          f"(confidence: {service_result['confidence']}%)")
    print(f"Reason: {service_result['reason']}")
    print(f"Alternative: {service_result['alternative_service']}")
    print()


def main():
    with open("data/sample_leads.json", "r", encoding="utf-8") as f:
        leads = json.load(f)

    for lead in leads:
        run_company(lead)


if __name__ == "__main__":
    main()
