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
print("  VERIFYING BUG FIX: SCREENSHOT & NON-FOOD REJECTION             ")
print("=================================================================\n")

# Test 1: The User's Exact Uploaded Screenshot
user_screenshot_path = "uploads/c655a63f92da4f07a7b0d2c6de6f8c60.png"
if os.path.exists(user_screenshot_path):
    with open(user_screenshot_path, "rb") as f:
        files = {"file": ("Screenshot 2025-08-23 184413.png", f.read(), "image/png")}
    r_user = requests.post(f"{BASE}/api/predict", files=files, data={"category": "General"}, headers=headers)
    print("1. User's Exact Screenshot Upload Test:")
    print(f"   HTTP Status:   {r_user.status_code}")
    print(f"   Response Body: {r_user.json()}")
    assert r_user.status_code == 422, f"Screenshot was not rejected with 422, got {r_user.status_code}"
    assert "This doesn't look like a food image" in r_user.json()["detail"], "Incorrect error message"
    print("   -> [PASS] Screenshot correctly blocked before classification!\n")

# Test 2: Document / Receipt
doc_img = np.full((300, 300, 3), 220, dtype=np.uint8)
cv2.putText(doc_img, "PAYMENT RECEIPT #9812", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
for y in range(80, 260, 30):
    cv2.line(doc_img, (20, y), (280, y), (80, 80, 80), 1)

_, doc_bytes = cv2.imencode(".jpg", doc_img)
files_doc = {"file": ("receipt.jpg", doc_bytes.tobytes(), "image/jpeg")}
r_doc = requests.post(f"{BASE}/api/predict", files=files_doc, data={"category": "General"}, headers=headers)
print("2. Document / Invoice Upload Test:")
print(f"   HTTP Status:   {r_doc.status_code}")
print(f"   Response Body: {r_doc.json()}")
assert r_doc.status_code == 422, "Document was not rejected with 422"
assert "This doesn't look like a food image" in r_doc.json()["detail"]
print("   -> [PASS] Document correctly rejected!\n")

# Test 3: Human Portrait / Clothing
face_img = np.full((300, 300, 3), (220, 220, 220), dtype=np.uint8)
cv2.circle(face_img, (150, 120), 60, (140, 175, 225), -1) # Skin tone
cv2.rectangle(face_img, (70, 190), (230, 300), (180, 50, 50), -1) # Shirt
cv2.circle(face_img, (130, 110), 6, (40, 40, 40), -1)
cv2.circle(face_img, (170, 110), 6, (40, 40, 40), -1)

_, face_bytes = cv2.imencode(".jpg", face_img)
files_face = {"file": ("portrait.jpg", face_bytes.tobytes(), "image/jpeg")}
r_face = requests.post(f"{BASE}/api/predict", files=files_face, data={"category": "General"}, headers=headers)
print("3. Human Portrait Upload Test:")
print(f"   HTTP Status:   {r_face.status_code}")
print(f"   Response Body: {r_face.json()}")
assert r_face.status_code == 422, "Portrait was not rejected with 422"
assert "This doesn't look like a food image" in r_face.json()["detail"]
print("   -> [PASS] Portrait correctly rejected!\n")

print("=================================================================")
print("  VERIFYING FOOD SAMPLES STILL PASS THROUGH AND PREDICT          ")
print("=================================================================\n")

test_cases = [
    ("sample_apple_fresh", "Fresh"),
    ("sample_banana_nearly_spoiled", "Nearly Spoiled"),
    ("sample_tomato_fresh", "Fresh"),
    ("sample_orange_spoiled", "Spoiled"),
    ("sample_bread_spoiled", "Spoiled"),
    ("sample_meat_fresh", "Fresh"),
]

for sample_id, expected_status in test_cases:
    r_food = requests.post(f"{BASE}/api/predict", data={"sample_id": sample_id, "category": "General"}, headers=headers)
    assert r_food.status_code == 200, f"Food sample {sample_id} failed with HTTP {r_food.status_code}"
    data = r_food.json()
    pred_status = data["freshness"]
    conf = data["confidence"]
    print(f"Sample: {sample_id}")
    print(f"   Expected: {expected_status} | Predicted: {pred_status} ({conf*100:.1f}% Conf) | Food Type: {data['food_type']}")
    assert pred_status == expected_status, f"Mismatch for {sample_id}"
    print(f"   -> [PASS] {pred_status} correctly classified!\n")

print("=================================================================")
print("  ALL VALIDATION AND CLASSIFICATION TESTS PASSED 100%!           ")
print("=================================================================")
