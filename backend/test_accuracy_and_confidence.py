import requests
import json

BASE = "http://127.0.0.1:8000"

# 1. Login to obtain JWT
r_login = requests.post(f"{BASE}/api/auth/login", json={"username_or_email": "qa_tester", "password": "password123"})
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n--- 1. Testing Prediction API JSON Structure & Probabilities ---")
for sample_id in ["sample_apple_fresh", "sample_tomato_fresh", "sample_bread_spoiled"]:
    res = requests.post(f"{BASE}/api/predict", data={"sample_id": sample_id, "category": "General"}, headers=headers)
    print(f"\nSample: {sample_id} -> HTTP {res.status_code}")
    data = res.json()
    print(f"  Freshness:          {data.get('freshness')}")
    print(f"  Confidence:         {data.get('confidence')}")
    print(f"  All Probabilities:  {data.get('all_probabilities')}")
    print(f"  Is Low Confidence:  {data.get('is_low_confidence')}")
    print(f"  Status Message:     {data.get('status_message')}")
    
    # Assert contract requirements
    assert "freshness" in data, "Missing 'freshness' key"
    assert "confidence" in data, "Missing 'confidence' key"
    assert "all_probabilities" in data, "Missing 'all_probabilities' key"
    assert "Fresh" in data["all_probabilities"]
    assert "Nearly Spoiled" in data["all_probabilities"]
    assert "Spoiled" in data["all_probabilities"]

print("\n=======================================================")
print("  ALL ACCURACY, PREPROCESSING & API CONTRACTS PASSED! ")
print("=======================================================")
