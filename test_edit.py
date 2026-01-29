#!/usr/bin/env python3
"""Test script to debug the edit session issue."""
import requests
import json
from datetime import datetime, timedelta
import time

BASE_URL = "http://localhost:8000"

def test_edit_session():
    """Test the complete flow of creating and editing a session."""
    
    # Wait for server to be ready
    time.sleep(2)
    
    print("Step 1: Starting a new session...")
    response = requests.post(
        f"{BASE_URL}/start",
        data={"category_id": "1", "description": "Test session"},
        allow_redirects=False
    )
    print(f"  Status: {response.status_code}")
    
    # Get the home page to extract session data
    print("\nStep 2: Fetching home page to get session data...")
    response = requests.get(f"{BASE_URL}/")
    print(f"  Status: {response.status_code}")
    
    # Find the session ID from the HTML
    import re
    session_match = re.search(r'data-session-id="(\d+)"', response.text)
    if session_match:
        session_id = session_match.group(1)
        print(f"  Found session ID: {session_id}")
        
        # Extract start time
        start_time_match = re.search(r'data-start-time="([^"]+)"', response.text)
        if start_time_match:
            start_time = start_time_match.group(1)
            print(f"  Start time from DB: {start_time}")
            
            # Now try to edit the session
            print(f"\nStep 3: Editing session {session_id}...")
            
            # Create new times - add 1 hour to start, 2 hours to end
            from dateutil import parser as date_parser
            start_dt = date_parser.isoparse(start_time)
            new_start = (start_dt + timedelta(minutes=0)).isoformat()
            new_end = (start_dt + timedelta(hours=1)).isoformat()
            
            # Remove milliseconds if present
            new_start = new_start.split('.')[0] + 'Z'
            new_end = new_end.split('.')[0] + 'Z'
            
            print(f"  New start time: {new_start}")
            print(f"  New end time: {new_end}")
            
            edit_response = requests.post(
                f"{BASE_URL}/sessions/{session_id}/edit",
                data={
                    "category_id": "1",
                    "description": "Updated test session",
                    "start_utc": new_start,
                    "end_utc": new_end,
                },
                allow_redirects=False
            )
            print(f"  Edit response status: {edit_response.status_code}")
            if edit_response.status_code != 303:
                print(f"  Error response: {edit_response.text}")
            else:
                print("  ✓ Edit successful!")
        else:
            print("  Could not find start time in HTML")
    else:
        print("  Could not find session ID in HTML")

if __name__ == "__main__":
    test_edit_session()
