import requests
import cv2
import numpy as np

BASE = "http://127.0.0.1:8000"

# 1. Login to get JWT
r_login = requests.post(f"{BASE}/api/auth/login", json={"username_or_email": "qa_tester", "password": "password123"})
token = r_login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=================================================================")
print("  LIVE API TEST: FOOD VS NON-FOOD FILTER VALIDATION              ")
print("=================================================================\n")

# Test 1: Upload a non-food text document (light grey background with black text)
doc_img = np.full((300, 300, 3), 220, dtype=np.uint8)
cv2.putText(doc_img, "PAYMENT RECEIPT #9812", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
for y in range(80, 260, 30):
    cv2.line(doc_img, (20, y), (280, y), (80, 80, 80), 1)

_, doc_bytes = cv2.imencode(".jpg", doc_img)
files_doc = {"file": ("receipt.jpg", doc_bytes.tobytes(), "image/jpeg")}
r_doc = requests.post(f"{BASE}/api/predict", files=files_doc, data={"category": "General"}, headers=headers)
print("Non-Food Document Test:")
print(f"  HTTP Status Code: {r_doc.status_code}")
print(f"  Response Body:    {r_doc.json()}")
assert r_doc.status_code == 422, "Non-food document was not rejected with 422"
assert "This doesn't look like a food image" in r_doc.json()["detail"], "Incorrect error message"
print("  -> [PASS] Document correctly rejected with non-food alert!\n")

# Test 2: Upload a human portrait / non-food clothing image
face_img = np.full((300, 300, 3), (220, 220, 220), dtype=np.uint8)
cv2.circle(face_img, (150, 120), 60, (140, 175, 225), -1) # Skin tone BGR
cv2.rectangle(face_img, (70, 190), (230, 300), (180, 50, 50), -1) # Blue shirt
cv2.circle(face_img, (130, 110), 6, (40, 40, 40), -1) # Eyes
cv2.circle(face_img, (170, 110), 6, (40, 40, 40), -1)
cv2.line(face_img, (130, 140), (170, 140), (40, 40, 180), 3) # Mouth

_, face_bytes = cv2.imencode(".jpg", face_img)
files_face = {"file": ("portrait.jpg", face_bytes.tobytes(), "image/jpeg")}
r_face = requests.post(f"{BASE}/api/predict", files=files_face, data={"category": "General"}, headers=headers)
print("Non-Food Human Portrait Test:")
print(f"  HTTP Status Code: {r_face.status_code}")
print(f"  Response Body:    {r_face.json()}")
assert r_face.status_code == 422, "Non-food portrait was not rejected with 422"
assert "This doesn't look like a food image" in r_face.json()["detail"], "Incorrect error message"
print("  -> [PASS] Portrait correctly rejected with non-food alert!\n")

# Test 3: Upload a metallic tool / electronic gadget with high sharpness
metal_img = np.full((300, 300, 3), (180, 180, 185), dtype=np.uint8)
for i in range(10, 290, 15):
    cv2.line(metal_img, (i, 10), (i, 290), (100, 100, 105), 1)
cv2.rectangle(metal_img, (50, 50), (250, 250), (60, 60, 65), 3)
cv2.circle(metal_img, (150, 150), 35, (230, 100, 30), -1) # Blue LED

_, metal_bytes = cv2.imencode(".jpg", metal_img)
files_metal = {"file": ("hardware.jpg", metal_bytes.tobytes(), "image/jpeg")}
r_metal = requests.post(f"{BASE}/api/predict", files=files_metal, data={"category": "General"}, headers=headers)
print("Non-Food Hardware Gadget Test:")
print(f"  HTTP Status Code: {r_metal.status_code}")
print(f"  Response Body:    {r_metal.json()}")
assert r_metal.status_code == 422, "Non-food hardware was not rejected with 422"
assert "This doesn't look like a food image" in r_metal.json()["detail"], "Incorrect error message"
print("  -> [PASS] Hardware correctly rejected with non-food alert!\n")

print("=================================================================")
print("  LIVE API TEST: FRESHNESS CLASSIFICATION ACCURACY               ")
print("=================================================================")

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
    print(f"  Expected: {expected_status} | Predicted: {pred_status} ({conf*100:.1f}% Conf)")
    assert pred_status == expected_status, f"Mismatch for {sample_id}: expected {expected_status}, got {pred_status}"
    print(f"  -> [PASS] {pred_status} correctly classified!\n")

print("=================================================================")
print("  ALL BUG 1 & BUG 2 LIVE VERIFICATION TESTS PASSED 100%!         ")
print("=================================================================")
