"""
Surmado Python SDK - Quick Start Example

Run this to test your API key and see the SDK in action.

Usage:
    export SURMADO_API_KEY=sur_live_xxx
    python examples/quickstart.py
"""
import os
from surmado import Surmado, SurmadoError, InsufficientCreditsError

def main():
    # Initialize client (reads SURMADO_API_KEY from env)
    client = Surmado()
    print("✓ Surmado client initialized")
    
    # Example 1: Run a Scan report
    print("\n--- Creating Scan Report ---")
    try:
        scan_result = client.scan(
            url="https://example.com",
            brand_name="Example Brand",
            email="you@example.com",  # Replace with your email
            tier="basic"
        )
        print(f"✓ Scan report created: {scan_result['report_id']}")
        print(f"  Status: {scan_result['status']}")
        print(f"  Credits used: {scan_result['credits_used']}")
    except InsufficientCreditsError:
        print("✗ Not enough credits. Top up at surmado.com")
        return
    except SurmadoError as e:
        print(f"✗ Error: {e}")
        return
    
    # Example 2: Run a Signal report
    print("\n--- Creating Signal Report ---")
    try:
        signal_result = client.signal(
            url="https://example.com",
            brand_name="Example Brand",
            email="you@example.com",  # Replace with your email
            industry="Technology",
            location="United States",
            persona="Developers and technical decision makers",
            pain_points="Finding reliable tools, integration complexity",
            brand_details="Developer-focused platform for building modern apps",
            direct_competitors="Vercel, Netlify, Heroku",
            tier="basic"
        )
        print(f"✓ Signal report created: {signal_result['report_id']}")
        print(f"  Token (for Solutions): {signal_result.get('token', 'N/A')}")
    except InsufficientCreditsError:
        print("✗ Not enough credits for Signal report")
    except SurmadoError as e:
        print(f"✗ Error: {e}")
    
    # Example 3: Check report status
    print("\n--- Checking Report Status ---")
    report = client.get_report(scan_result["report_id"])
    print(f"Report {report['report_id']}:")
    print(f"  Status: {report['status']}")
    print(f"  Product: {report['product']}")
    
    # Example 4: Wait for completion (optional - takes ~15 min)
    # Uncomment to wait for the report to complete:
    #
    # print("\n--- Waiting for Report ---")
    # completed = client.wait_for_report(scan_result["report_id"])
    # print(f"✓ Report completed!")
    # print(f"  PDF: {completed.get('download_url', 'N/A')}")
    # print(f"  JSON: {completed.get('intelligence_download_url', 'N/A')}")
    
    print("\n✓ Done! Reports are processing (~15 min).")
    print("  Check status: client.get_report(report_id)")
    print("  Or add webhook_url to receive POST when complete.")


if __name__ == "__main__":
    main()

