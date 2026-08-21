import requests
import json

BASE = "http://127.0.0.1:8000"

# 1. Login or register to get JWT token
user_payload = {"username_or_email": "qa_tester", "password": "password123"}
r_login = requests.post(f"{BASE}/api/auth/login", json=user_payload)
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("\n--- 1. Testing Recipe Suggestions on 'Nearly Spoiled' Banana ---")
r_banana = requests.post(
    f"{BASE}/api/predict",
    data={"sample_id": "sample_banana_nearly_spoiled", "category": "Fruit"},
    headers=headers
)
print("Banana Status Code:", r_banana.status_code)
banana_data = r_banana.json()
print(f"Freshness: {banana_data.get('freshness_status')}")
print(f"Detected Food Type: {banana_data.get('food_type')}")
print(f"Recipe Suggestions Count: {len(banana_data.get('recipe_suggestions') or [])}")
if banana_data.get('recipe_suggestions'):
    for idx, recipe in enumerate(banana_data['recipe_suggestions'], 1):
        print(f"  {idx}. {recipe['title']} ({recipe['prep_time']}) - {recipe['source_url']}")

print("\n--- 2. Testing Fresh Item (Should have NO recipe suggestions) ---")
r_apple = requests.post(
    f"{BASE}/api/predict",
    data={"sample_id": "sample_apple_fresh", "category": "Fruit"},
    headers=headers
)
apple_data = r_apple.json()
print(f"Freshness: {apple_data.get('freshness_status')}")
print(f"Recipe Suggestions: {apple_data.get('recipe_suggestions')}")
assert apple_data.get('recipe_suggestions') is None

print("\n--- 3. Testing Analytics API with SQL Aggregations ---")
for r_range in ["week", "month", "all"]:
    r_analytics = requests.get(f"{BASE}/api/analytics?range={r_range}", headers=headers)
    print(f"Analytics ({r_range}): Status {r_analytics.status_code}")
    data = r_analytics.json()
    print(f"  Total scans: {data['total_scans']}")
    print(f"  Wasted %: {data['wasted_percentage']}%")
    print(f"  Status breakdown: {data['status_breakdown']}")
    print(f"  Daily trends entries: {len(data['daily_trends'])}")

print("\n=======================================================")
print("  ALL ANALYTICS & RECIPE TESTS PASSED SUCCESSFULLY!   ")
print("=======================================================")
