import os
import sys
import time
from graph import graph
from crawler import CrawlError

TEST_CASES = [
    {
        "name": "1. Simple Static Website",
        "url": "https://example.com",
        "expected_error": None
    },
    {
        "name": "2. Technology / News Page",
        "url": "https://blog.python.org",
        "expected_error": None
    },
    {
        "name": "3. Product Page",
        "url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        "expected_error": None
    },
    {
        "name": "4. Research Paper Page",
        "url": "https://arxiv.org/abs/2312.00752",
        "expected_error": None
    },
    {
        "name": "5. Business Directory / Listing Page",
        "url": "https://scrapethissite.com/pages/simple/",
        "expected_error": None
    },
    {
        "name": "6. Invalid URL & DNS Failure",
        "url": "https://nonexistent-domain-xyz-987456123.org",
        "expected_error": "DNS_FAILURE"
    }
]

def run_all_tests():
    print("=" * 60)
    print("RUNNING END-TO-END PIPELINE VALIDATION SUITE")
    print("=" * 60)

    success_count = 0

    for tc in TEST_CASES:
        name = tc["name"]
        url = tc["url"]
        exp_err = tc["expected_error"]

        print(f"\n--- [TEST] {name} ---")
        print(f"Target: {url}")

        initial_state = {
            "url": url,
            "plan": {},
            "raw_html": "",
            "extracted_data": {},
            "cleaned_data": {},
            "summary": "",
            "report_path": "",
            "retry_count": 0
        }

        try:
            result = graph.invoke(initial_state)

            if exp_err:
                print(f"FAIL: Expected error '{exp_err}', but execution succeeded unexpectedly.")
                continue

            plan = result.get("plan", {})
            cleaned = result.get("cleaned_data", {})
            summary = result.get("summary", "")

            # Assertions
            assert plan, "Plan is empty!"
            assert "page_type" in plan, "Plan missing 'page_type'!"
            assert "fields" in plan and isinstance(plan["fields"], list), "Plan fields missing or not list!"
            assert "source_url" in plan["fields"], "Mandatory 'source_url' missing from plan fields!"
            assert "summary" in plan["fields"], "Mandatory 'summary' missing from plan fields!"

            assert cleaned, "Cleaned data is empty!"
            assert cleaned.get("source_url") == url, f"Cleaned source_url does not match input URL! ({cleaned.get('source_url')} != {url})"
            assert summary, "Summary is empty!"

            # Verify files
            assert os.path.exists("output/extracted_data.csv"), "CSV report not created!"
            assert os.path.exists("output/extracted_data.json"), "JSON report not created!"
            assert os.path.exists("output/extracted_report.pdf"), "PDF report not created!"

            assert os.path.getsize("output/extracted_data.csv") > 10, "CSV report is empty!"
            assert os.path.getsize("output/extracted_data.json") > 10, "JSON report is empty!"
            assert os.path.getsize("output/extracted_report.pdf") > 100, "PDF report is empty!"

            print(f"PASS: {name}")
            print(f"  -> Page Type: {plan.get('page_type')}")
            print(f"  -> Dynamic Fields: {plan.get('fields')}")
            print(f"  -> Summary: {summary[:120]}...")
            success_count += 1

        except CrawlError as ce:
            if exp_err and exp_err in str(ce.error_type):
                print(f"PASS: {name} gracefully caught expected CrawlError: [{ce.error_type}] {ce.message}")
                success_count += 1
            else:
                print(f"CrawlError: [{ce.error_type}] {ce.message}")
        except Exception as e:
            if exp_err and exp_err in str(e):
                print(f"PASS: {name} gracefully caught expected error: {e}")
                success_count += 1
            else:
                print(f"FAIL: Unexpected exception during {name}: {e}")

        time.sleep(1)

    print("\n" + "=" * 60)
    print(f"RESULTS: {success_count}/{len(TEST_CASES)} tests passed.")
    print("=" * 60)

    return success_count == len(TEST_CASES)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
