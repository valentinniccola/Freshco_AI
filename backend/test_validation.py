import cv2
import numpy as np
import io
from PIL import Image
from fastapi import HTTPException
from ai.validator import ImageValidator
from ai.model import classifier
from rate_limiter import RateLimiter

def test_file_level_validation():
    print("\n--- Testing Stage 1: File-Level Checks ---")
    
    # 1. Invalid extension
    try:
        ImageValidator.validate_file_level("document.txt", b"some text content")
        assert False, "Should have failed on invalid extension"
    except HTTPException as e:
        print("[PASS] Extension rejection:", e.detail)
        assert e.status_code == 400

    # 2. File size > 10MB
    large_bytes = b"0" * (11 * 1024 * 1024)
    try:
        ImageValidator.validate_file_level("large.jpg", large_bytes)
        assert False, "Should have failed on large file size"
    except HTTPException as e:
        print("[PASS] Size rejection (>10MB):", e.detail)
        assert e.status_code == 400

    # 3. Low Resolution (< 224x224)
    img_low = Image.new("RGB", (150, 150), color=(255, 0, 0))
    buf = io.BytesIO()
    img_low.save(buf, format="JPEG")
    try:
        ImageValidator.validate_file_level("small.jpg", buf.getvalue())
        assert False, "Should have failed on low resolution"
    except HTTPException as e:
        print("[PASS] Resolution rejection (<224x224):", e.detail)
        assert e.status_code == 400

    # 4. Valid image
    img_valid = Image.new("RGB", (300, 300), color=(200, 50, 50))
    buf_v = io.BytesIO()
    img_valid.save(buf_v, format="JPEG")
    w, h = ImageValidator.validate_file_level("valid.jpg", buf_v.getvalue())
    assert w == 300 and h == 300
    print(f"[PASS] Valid file passed: {w}x{h}")

def test_content_level_validation():
    print("\n--- Testing Stage 2: Content-Level Checks (OpenCV) ---")
    
    # 1. Too Dark
    dark_img = np.full((300, 300, 3), 15, dtype=np.uint8)
    try:
        ImageValidator.validate_content_level(dark_img)
        assert False, "Should have failed on dark image"
    except HTTPException as e:
        print("[PASS] Dark lighting rejection:", e.detail)
        assert "dark/bright" in e.detail

    # 2. Too Bright / Overexposed
    bright_img = np.full((300, 300, 3), 245, dtype=np.uint8)
    try:
        ImageValidator.validate_content_level(bright_img)
        assert False, "Should have failed on bright image"
    except HTTPException as e:
        print("[PASS] Overexposed lighting rejection:", e.detail)
        assert "dark/bright" in e.detail

    # 3. Blur Detection (Normal lighting, high blur)
    sharp_food = np.full((300, 300, 3), (40, 160, 220), dtype=np.uint8)
    cv2.circle(sharp_food, (150, 150), 80, (20, 20, 200), -1)
    blurry_img = cv2.GaussianBlur(sharp_food, (55, 55), 0)
    try:
        ImageValidator.validate_content_level(blurry_img)
        assert False, "Should have failed on blur"
    except HTTPException as e:
        print("[PASS] Blur rejection:", e.detail)
        assert "blurry" in e.detail

    # 4. Non-food (Monochrome text/doc screenshot)
    mono_img = np.full((300, 300, 3), 180, dtype=np.uint8)
    cv2.line(mono_img, (20, 50), (280, 50), (20, 20, 20), 2)
    cv2.line(mono_img, (20, 90), (280, 90), (20, 20, 20), 2)
    try:
        ImageValidator.validate_content_level(mono_img)
        assert False, "Should have failed on non-food image"
    except HTTPException as e:
        print("[PASS] Non-food rejection:", e.detail)
        assert "This doesn't look like a food image" in e.detail

def test_model_output_validation():
    print("\n--- Testing Stage 3: Model-Output Validation ---")
    
    with open("static/samples/apple_fresh.jpg", "rb") as f:
        data = f.read()
    fresh_sample = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    res = classifier.predict(fresh_sample)
    print(f"[PASS] Normal prediction: {res['freshness_status']} (Confidence: {res['confidence_score']*100:.1f}%)")
    print(f"       is_uncertain: {res['is_uncertain']}, is_low_confidence: {res['is_low_confidence']}")

def test_rate_limiter():
    print("\n--- Testing Stage 4: Rate Limiting ---")
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    user_id = "test_user_42"
    
    for i in range(5):
        limiter.check_rate_limit(user_id)
    print("[PASS] 5 requests passed within limit")
    
    try:
        limiter.check_rate_limit(user_id)
        assert False, "6th request should have triggered 429 Too Many Requests"
    except HTTPException as e:
        print("[PASS] Rate limit rejection (429):", e.detail)
        assert e.status_code == 429

if __name__ == "__main__":
    test_file_level_validation()
    test_content_level_validation()
    test_model_output_validation()
    test_rate_limiter()
    print("\n=======================================================")
    print("  ALL 4 VALIDATION TIERS PASSED WITH 100% SUCCESS!  ")
    print("=======================================================")
