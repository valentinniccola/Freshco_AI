import requests
import time
import sqlite3
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
DB_PATH = Path(__file__).resolve().parent / "freshco.db"

def test_all_auth_features():
    print("=" * 70)
    print("  RUNNING AUTHENTICATION & FORGOT PASSWORD INTEGRATION TESTS  ")
    print("=" * 70)

    test_timestamp = int(time.time())
    test_username = f"user_{test_timestamp}"
    test_email = f"test_{test_timestamp}@example.com"
    initial_password = "InitialPassword123!"
    new_password = "BrandNewSecurePassword456!"
    valid_phone = "+1 (555) 234-5678"
    invalid_phone = "invalid_phone_123"

    # Test 1: Invalid Phone Number Rejection
    print("\n[Test 1] Testing Registration with Invalid Phone Number...")
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": f"{test_username}_bad",
        "email": f"bad_{test_email}",
        "password": initial_password,
        "phone_number": invalid_phone
    })
    print(f"  Status Code: {res.status_code}")
    assert res.status_code in [400, 422], f"Expected 400/422 on invalid phone, got {res.status_code}"
    print("  [PASS] Invalid phone format correctly rejected by Pydantic validator.")

    # Test 2: Valid Registration with Optional Phone Number
    print("\n[Test 2] Testing Registration with Valid Phone Number...")
    res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": test_username,
        "email": test_email,
        "password": initial_password,
        "phone_number": valid_phone
    })
    print(f"  Status Code: {res.status_code}")
    assert res.status_code == 200, f"Expected 200 on valid registration, got {res.status_code}: {res.text}"
    user_data = res.json()["user"]
    assert user_data["phone_number"] == valid_phone, f"Expected phone '{valid_phone}', got '{user_data.get('phone_number')}'"
    print(f"  [PASS] User registered successfully with phone: {user_data['phone_number']}")

    # Test 3: Login with Initial Password
    print("\n[Test 3] Testing Login with Initial Credentials...")
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": test_username,
        "password": initial_password
    })
    assert res.status_code == 200, f"Expected 200 on login, got {res.status_code}: {res.text}"
    print("  [PASS] Initial login successful.")

    # Test 4: Request Password Reset Code
    print("\n[Test 4] Testing Forgot Password Code Request...")
    res = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={
        "email": test_email
    })
    assert res.status_code == 200, f"Expected 200 on forgot-password request, got {res.status_code}: {res.text}"
    print(f"  Response: {res.json()['message']}")
    print("  [PASS] Password reset code request returned 200.")

    # Retrieve generated code from SQLite DB for testing
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT code, expires_at, used FROM password_reset_codes WHERE email = ? ORDER BY id DESC LIMIT 1;",
        (test_email,)
    )
    row = cursor.fetchone()
    conn.close()
    assert row is not None, "Expected reset code to be saved in DB"
    code, expires_at, used = row
    print(f"  Retrieved Code from DB: {code} (Used: {bool(used)})")
    assert len(code) == 6 and code.isdigit(), f"Expected 6-digit numeric code, got '{code}'"
    assert not used, "Expected newly generated code to be unused"

    # Test 5: Verify Rejection of Invalid Verification Code
    print("\n[Test 5] Testing Reset with Incorrect Code (000000)...")
    res = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": test_email,
        "code": "000000",
        "new_password": new_password
    })
    assert res.status_code == 400, f"Expected 400 on invalid code, got {res.status_code}: {res.text}"
    print(f"  [PASS] Incorrect code rejected with 400: {res.json()['detail']}")

    # Test 6: Successful Password Reset with Valid Code
    print("\n[Test 6] Testing Password Reset with Valid Code...")
    res = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": test_email,
        "code": code,
        "new_password": new_password
    })
    assert res.status_code == 200, f"Expected 200 on valid reset, got {res.status_code}: {res.text}"
    print(f"  [PASS] Password reset succeeded: {res.json()['message']}")

    # Test 7: Enforce Single-Use Security (Attempting to Reuse Same Code)
    print("\n[Test 7] Testing Replay Attack / Reusing Already Used Code...")
    res = requests.post(f"{BASE_URL}/api/auth/forgot-password/reset", json={
        "email": test_email,
        "code": code,
        "new_password": "AnotherPassword999!"
    })
    assert res.status_code == 400, f"Expected 400 on already used code, got {res.status_code}: {res.text}"
    print(f"  [PASS] Reused code immediately rejected (single-use enforced): {res.json()['detail']}")

    # Test 8: Verify Old Password No Longer Works
    print("\n[Test 8] Testing Login with Old Password...")
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": test_username,
        "password": initial_password
    })
    assert res.status_code == 401, f"Expected 401 on old password, got {res.status_code}"
    print("  [PASS] Old password immediately deactivated.")

    # Test 9: Verify Login with New Password Works
    print("\n[Test 9] Testing Login with New Password...")
    res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username_or_email": test_username,
        "password": new_password
    })
    assert res.status_code == 200, f"Expected 200 on login with new password, got {res.status_code}: {res.text}"
    print(f"  [PASS] Login with new password succeeded! Received JWT Token.")

    # Test 10: Rate Limiting Enforcement (Max 3 requests / hour)
    print("\n[Test 10] Testing Rate Limiting (Sending 3 more requests to hit limit)...")
    req_res_1 = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": test_email})
    req_res_2 = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": test_email})
    req_res_3 = requests.post(f"{BASE_URL}/api/auth/forgot-password/request", json={"email": test_email})
    print(f"  4th Request Status Code: {req_res_3.status_code}")
    assert req_res_3.status_code == 429, f"Expected 429 Too Many Requests, got {req_res_3.status_code}: {req_res_3.text}"
    print(f"  [PASS] Rate limit strictly enforced: {req_res_3.json()['detail']}")

    print("\n" + "=" * 70)
    print("  ALL 10 AUTHENTICATION & PASSWORD RESET TESTS PASSED!  ")
    print("=" * 70)

if __name__ == "__main__":
    test_all_auth_features()
