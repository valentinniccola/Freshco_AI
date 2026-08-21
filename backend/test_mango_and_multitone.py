import requests
import cv2
import numpy as np
import os

BASE = "http://127.0.0.1:8000"

# 1. Obtain Auth Token
r_login = requests.post(f"{BASE}/api/auth/login", json={"username_or_email": "qa_tester", "password": "password123"})
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=================================================================")
print("  TESTING FIXED MANGO & MULTI-TONE RIPENING ACCURACY             ")
print("=================================================================\n")

# Test 1: User's Exact Mango Upload
mango_path = "uploads/f3efeb533c6e4ea4b36f47ebfab252ac.jpg"
if os.path.exists(mango_path):
    with open(mango_path, "rb") as f:
        files = {"file": ("stock_mango.jpg", f.read(), "image/jpeg")}
    r_mango = requests.post(f"{BASE}/api/predict", files=files, data={"category": "Fruit"}, headers=headers)
    assert r_mango.status_code == 200, f"Mango prediction failed with {r_mango.status_code}"
    data = r_mango.json()
    print("1. User's Exact Uploaded Stock Mango Test:")
    print(f"   Food Type:        {data['food_type']}")
    print(f"   Freshness Status: {data['freshness']} ({data['confidence']*100:.1f}% Conf)")
    print(f"   Defect Metrics:   Spot={data['defect_metrics']['spot_coverage_pct']}%, Browning={data['defect_metrics']['browning_score']}, Discoloration={data['defect_metrics']['discoloration_index']}")
    print(f"   Shelf-Life:       {data['shelf_life_desc']}")
    assert data["food_type"] == "mango", f"Expected mango, got {data['food_type']}"
    assert data["freshness"] == "Fresh", f"Expected Fresh, got {data['freshness']}"
    assert data["defect_metrics"]["spot_coverage_pct"] < 5.0, "Spot coverage too high for fresh mango"
    print("   -> [PASS] Stock Mango correctly identified as Fresh Mango!\n")

# Test 2: Ripe Peach (Multi-tone blush)
peach_img = np.full((256, 256, 3), 245, dtype=np.uint8)
cv2.circle(peach_img, (128, 128), 80, (70, 180, 245), -1) # Yellow base
cv2.circle(peach_img, (105, 105), 55, (100, 110, 235), -1) # Pink blush
_, peach_bytes = cv2.imencode(".jpg", peach_img)
files_peach = {"file": ("ripe_peach.jpg", peach_bytes.tobytes(), "image/jpeg")}
r_peach = requests.post(f"{BASE}/api/predict", files=files_peach, data={"category": "Fruit"}, headers=headers)
assert r_peach.status_code == 200
data_peach = r_peach.json()
print("2. Multi-tone Ripe Peach Test:")
print(f"   Food Type:        {data_peach['food_type']}")
print(f"   Freshness Status: {data_peach['freshness']} ({data_peach['confidence']*100:.1f}% Conf)")
print(f"   Defect Metrics:   Spot={data_peach['defect_metrics']['spot_coverage_pct']}%, Browning={data_peach['defect_metrics']['browning_score']}")
assert data_peach["freshness"] == "Fresh"
print("   -> [PASS] Ripe Peach correctly classified as Fresh!\n")

# Test 3: Standard Fresh and Spoiled Benchmarks
test_samples = [
    ("sample_apple_fresh", "Fresh", "apple"),
    ("sample_banana_nearly_spoiled", "Nearly Spoiled", "banana"),
    ("sample_tomato_fresh", "Fresh", "tomato"),
    ("sample_orange_spoiled", "Spoiled", "orange"),
    ("sample_bread_spoiled", "Spoiled", "bread"),
    ("sample_meat_fresh", "Fresh", "meat"),
]

print("3. Benchmark Samples Regression Check:")
for sample_id, expected_status, expected_food in test_samples:
    r_sample = requests.post(f"{BASE}/api/predict", data={"sample_id": sample_id, "category": "General"}, headers=headers)
    assert r_sample.status_code == 200
    data_s = r_sample.json()
    print(f"   {sample_id:<30} -> Food: {data_s['food_type']:<8} | Status: {data_s['freshness']:<14} ({data_s['confidence']*100:.1f}%)")
    assert data_s["freshness"] == expected_status, f"Mismatch for {sample_id}: expected {expected_status}, got {data_s['freshness']}"
    assert data_s["food_type"] == expected_food, f"Mismatch food type for {sample_id}: expected {expected_food}, got {data_s['food_type']}"

print("\n=================================================================")
print("  ALL MANGO, MULTI-TONE, AND BENCHMARK TESTS PASSED 100%!        ")
print("=================================================================")
