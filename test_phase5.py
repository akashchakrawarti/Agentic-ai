"""
test_phase5.py
---------------
Tests the web research tool on:
  1. A real, well-known company (should find real results)
  2. A made-up company name (should gracefully report "no results",
     NOT invent information)

Run with:  python test_phase5.py
"""

from research import research_company, is_research_available


def print_research_result(company_name: str, result: dict):
    print(f"\nCOMPANY: {company_name}")
    print(f"Status: {result['status']}")
    print(f"\nSummary:\n{result['summary']}")

    if result["raw_snippets"]:
        print(f"\nRaw sources used ({len(result['raw_snippets'])}):")
        for s in result["raw_snippets"]:
            print(f"  - {s['title']} ({s['url']})")


def main():
    print(f"Research available: {is_research_available()}")
    if not is_research_available():
        print(
            "\nNo TAVILY_API_KEY found in .env - this test will show the "
            "graceful fallback behavior for ALL queries below, which is "
            "expected and correct if you haven't added a Tavily key yet.\n"
        )

    print("=" * 70)
    print("TEST 1: Real, well-known company")
    print("=" * 70)
    result = research_company("Infosys", website="infosys.com")
    print_research_result("Infosys", result)

    print("\n" + "=" * 70)
    print("TEST 2: Made-up company name (should NOT invent information)")
    print("=" * 70)
    result = research_company("Zzqxplor Nonexistent Ventures Pvt Ltd")
    print_research_result("Zzqxplor Nonexistent Ventures Pvt Ltd", result)


if __name__ == "__main__":
    main()
