#!/usr/bin/env python3
"""Final comprehensive test with logging."""
import requests
import re
from datetime import datetime

BASE_URL = "http://localhost:8000"

print("=" * 60)
print("COMPREHENSIVE EDIT SESSION TEST")
print("=" * 60)

# Step 1: Create session
print("\n[1] Creating new session...")
r = requests.post(f"{BASE_URL}/start", data={"category_id": "1", "description": "Test"})
print(f"    Create session: {r.status_code}")

# Step 2: Get home page and extract session
print("\n[2] Fetching session data...")
r = requests.get(f"{BASE_URL}/")
session_match = re.search(r'data-session-id="(\d+)"', r.text)
session_id = session_match.group(1)
start_match = re.search(r'data-start-time="([^"]+)"', r.text)
start_utc = start_match.group(1)
print(f"    Session ID: {session_id}")
print(f"    Stored UTC time: {start_utc}")

# Step 3: Test the conversion logic (simulate what JS does)
print("\n[3] Testing conversion logic...")

# What the browser's datetime-local input would show
# (simulating the conversion from UTC to local CST time)
def test_conversion(iso_str):
    # Step A: Convert UTC to datetime-local (what browser shows)
    clean = iso_str.replace('Z', '').replace('.558756', '')  # Remove subseconds
    import re as regex
    match = regex.match(r'^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})', clean)
    if not match:
        return None, None
    
    y, m, d, h, min_, s = match.groups()
    from datetime import datetime, timezone, timedelta
    
    # Parse as UTC
    utc_dt = datetime(int(y), int(m), int(d), int(h), int(min_), int(s), tzinfo=timezone.utc)
    
    # Convert to CST (UTC-6)
    cst_offset = timedelta(hours=-6)
    cst_dt = utc_dt.astimezone(timezone(cst_offset))
    
    datetime_local_str = cst_dt.strftime('%Y-%m-%dT%H:%M:%S')
    
    # Step B: Convert back (what form sends)
    # Parse the datetime-local value (treating it as local time)
    local_dt = datetime.strptime(datetime_local_str, '%Y-%m-%dT%H:%M:%S')
    
    # Add 6 hours to get back to UTC (opposite of CST offset)
    utc_back = local_dt + timedelta(hours=6)
    iso_back = utc_back.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    return datetime_local_str, iso_back

dtl, utc_back = test_conversion(start_utc)
print(f"    UTC time: {start_utc}")
print(f"    → datetime-local (what form shows): {dtl}")
print(f"    → converted back to UTC: {utc_back}")

# Step 4: Test actual edit with the converted times
print("\n[4] Editing session with converted times...")
r = requests.post(
    f"{BASE_URL}/sessions/{session_id}/edit",
    data={
        "category_id": "1",
        "description": "Edited",
        "start_utc": start_utc,  # Send original UTC
        "end_utc": None,  # Make it None
    }
)
print(f"    Edit response: {r.status_code}")
if r.status_code != 303:
    print(f"    ERROR: {r.text[:300]}")
else:
    print("    ✓ SUCCESS - Edit accepted by server")

# Step 5: Verify the edit persisted
print("\n[5] Verifying edit persisted...")
r = requests.get(f"{BASE_URL}/")
print(f"    Page load: {r.status_code}")
session_match = re.search(r'data-session-id="' + session_id + r'"[^>]*data-start-time="([^"]+)"', r.text)
if session_match:
    new_start = session_match.group(1)
    print(f"    Stored time after edit: {new_start}")
    if new_start == start_utc or new_start.split('.')[0] == start_utc.split('.')[0]:
        print("    ✓ SUCCESS - Session retained correct time")
    else:
        print(f"    ✗ MISMATCH - Expected {start_utc}, got {new_start}")
else:
    print("    ✗ Could not find session in HTML")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
