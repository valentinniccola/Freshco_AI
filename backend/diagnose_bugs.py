import cv2
import numpy as np
from PIL import Image
from ai.preprocessor import ImagePreprocessor
from ai.model import classifier
from ai.validator import ImageValidator

samples = [
    ("apple_fresh.jpg", "Fresh"),
    ("banana_spotted.jpg", "Nearly Spoiled"),
    ("tomato_fresh.jpg", "Fresh"),
    ("orange_spoiled.jpg", "Spoiled"),
    ("bread_spoiled.jpg", "Spoiled"),
    ("meat_fresh.jpg", "Fresh"),
]

print("=================================================================")
print("  DIAGNOSTIC REPORT: FRESHNESS PREDICTIONS & FEATURE METRICS     ")
print("=================================================================\n")

for filename, expected in samples:
    path = f"static/samples/{filename}"
    img_bgr = cv2.imread(path)
    if img_bgr is None:
        print(f"Error loading {path}")
        continue
    
    # 1. Defect metrics without and with CLAHE
    metrics = ImagePreprocessor.extract_visual_defect_metrics(img_bgr)
    
    # 2. Prediction
    pred = classifier.predict(img_bgr)
    
    print(f"--- Sample: {filename} (Expected: {expected}) ---")
    print(f"  Predicted Label:     {pred['freshness']}")
    print(f"  Confidence:          {pred['confidence']:.4f}")
    print(f"  All Probabilities:   {pred['all_probabilities']}")
    print(f"  Defect Metrics:      Spot Coverage={metrics['spot_coverage_pct']}%, Browning={metrics['browning_score']}, Discoloration={metrics['discoloration_index']}, Homogeneity={metrics['surface_homogeneity']}%")
    match = "MATCH" if pred['freshness'] == expected else "MISMATCH"
    print(f"  Result Status:       [{match}]\n")

print("\n=================================================================")
print("  DIAGNOSTIC REPORT: FOOD VS NON-FOOD VALIDATION                 ")
print("=================================================================\n")

# Test synthetic non-food images
# 1. Document / Text image (white with black lines)
doc_img = np.full((300, 300, 3), 255, dtype=np.uint8)
cv2.putText(doc_img, "INVOICE #1024", (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
for y in range(80, 260, 25):
    cv2.line(doc_img, (20, y), (280, y), (50, 50, 50), 1)

# 2. Metallic / Gadget object (Silver/Grey with blue LED)
metal_img = np.full((300, 300, 3), (180, 180, 185), dtype=np.uint8)
cv2.rectangle(metal_img, (50, 50), (250, 250), (120, 120, 125), -1)
cv2.circle(metal_img, (150, 150), 30, (230, 100, 30), -1) # Blue LED

# 3. Portrait / Face silhouette (Skin tone with hair and shirt)
face_img = np.full((300, 300, 3), (220, 220, 220), dtype=np.uint8)
cv2.circle(face_img, (150, 120), 60, (140, 175, 225), -1) # Skin tone BGR
cv2.rectangle(face_img, (70, 190), (230, 300), (180, 50, 50), -1) # Blue shirt

test_non_foods = [
    ("Document / Invoice Text", doc_img),
    ("Metallic Gadget / Hardware", metal_img),
    ("Human Portrait / Clothing", face_img),
]

for name, img in test_non_foods:
    is_food, conf = ImageValidator._verify_food_content(img)
    print(f"Non-food Test: '{name}' -> is_food = {is_food} (confidence = {conf})")
    if is_food:
        print(f"  [BUG DETECTED] Non-food image was INCORRECTLY accepted as food!")
    else:
        print(f"  [OK] Successfully rejected non-food image.")
