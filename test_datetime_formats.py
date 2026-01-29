#!/usr/bin/env python3
"""Test script to simulate browser form submission with datetime-local values."""
import requests
import time

BASE_URL = "http://localhost:8000"

def test_with_datetime_local_format():
    """Test using the exact format that browser datetime-local sends."""
    
    print("Step 1: Create a session...")
    response = requests.post(
        f"{BASE_URL}/start",
        data={"category_id": "1", "description": "Test"},
        allow_redirects=False
    )
    print(f"  Status: {response.status_code}")
    
    # Get page to find session ID
    response = requests.get(f"{BASE_URL}/")
    import re
    session_match = re.search(r'data-session-id="(\d+)"', response.text)
    session_id = session_match.group(1)
    print(f"  Session ID: {session_id}")
    
    # Now edit with datetime-local format (YYYY-MM-DDTHH:MM:SS)
    # This is what the browser form sends
    print("\nStep 2: Edit with datetime-local format...")
    print("  Testing various datetime-local formats...")
    
    test_cases = [
        ("2026-01-27T15:53:55", "2026-01-27T16:53:55"),  # Simple format
        ("2026-01-27T15:53:55Z", "2026-01-27T16:53:55Z"),  # With Z
    ]
    
    for i, (start, end) in enumerate(test_cases):
        print(f"\n  Test case {i+1}: start={start}, end={end}")
        response = requests.post(
            f"{BASE_URL}/sessions/{session_id}/edit",
            data={
                "category_id": "1",
                "description": "Updated",
                "start_utc": start,
                "end_utc": end,
            },
            allow_redirects=False
        )
        print(f"    Status: {response.status_code}")
        if response.status_code != 303:
            print(f"    Error: {response.text[:200]}")

if __name__ == "__main__":
    test_with_datetime_local_format()
