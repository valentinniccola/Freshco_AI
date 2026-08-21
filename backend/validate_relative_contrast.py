import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
from ai.preprocessor import ImagePreprocessor
from ai.model import classifier

def run_all_validation_tests():
    print("=================================================================")
    print("  COMPREHENSIVE VALIDATION: RELATIVE-CONTRAST DEFECT EXTRACTION  ")
    print("=================================================================\n")

    # =========================================================================
    # 1. GROUP 1: FRESH FOOD TEST SET (5 IMAGES)
    # =========================================================================
    print("-----------------------------------------------------------------")
    print("TEST 1: FRESH FOOD IMAGES (MUST HAVE NEAR-0% DEFECTS & BE FRESH)")
    print("-----------------------------------------------------------------")
    
    apple_img = cv2.imread("static/samples/apple_fresh.jpg")
    tomato_img = cv2.imread("static/samples/tomato_fresh.jpg")
    steak_img = cv2.imread("static/samples/meat_fresh.jpg")

    banana_clean = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.ellipse(banana_clean, (128, 128), (85, 32), -25, 0, 360, (40, 215, 245), -1)
    
    granny_smith = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.circle(granny_smith, (128, 128), 75, (50, 200, 80), -1)

    fresh_group = [
        ("Fuji Apple (apple_fresh.jpg)", apple_img, "Fruit"),
        ("Vine Tomato (tomato_fresh.jpg)", tomato_img, "Vegetable"),
        ("Clean Yellow Banana", banana_clean, "Fruit"),
        ("Granny Smith Apple", granny_smith, "Fruit"),
        ("Beef Steak (meat_fresh.jpg)", steak_img, "Meat"),
    ]

    print(f"{'Image / Food Item':<32} | {'Spot %':<8} | {'Brown':<6} | {'Confidence':<12} | {'Final Label'}")
    print("-" * 75)
    for name, img, cat in fresh_group:
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img, category_hint=cat)
        pred = classifier.predict(img, category_hint=cat)
        print(f"{name:<32} | {metrics['spot_coverage_pct']:>6.2f}% | {metrics['browning_score']:>5.2f} | {pred['confidence']*100:>9.1f}% | {pred['freshness']}")
        assert pred['freshness'] == 'Fresh', f"Failed for {name}: expected Fresh, got {pred['freshness']}"

    # =========================================================================
    # 2. GROUP 2: GENUINELY NEARLY SPOILED (5) & GENUINELY SPOILED (5)
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("TEST 2A: GENUINELY NEARLY SPOILED IMAGES (MUST STILL BE NEARLY SPOILED)")
    print("-----------------------------------------------------------------")
    
    banana_spotted = cv2.imread("static/samples/banana_spotted.jpg")
    
    cut_apple_brown = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.circle(cut_apple_brown, (128, 128), 80, (215, 235, 200), -1)
    cv2.ellipse(cut_apple_brown, (110, 110), (25, 15), 30, 0, 360, (70, 120, 170), -1)
    cv2.ellipse(cut_apple_brown, (150, 140), (20, 12), -20, 0, 360, (70, 120, 170), -1)
    
    aged_banana_skin = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.ellipse(aged_banana_skin, (128, 128), (85, 32), -25, 0, 360, (40, 195, 220), -1)
    for sx, sy in [(100, 110), (140, 95), (155, 140), (115, 150), (130, 125)]:
        cv2.circle(aged_banana_skin, (sx, sy), 7, (20, 25, 35), -1)
        
    stale_bread = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.rectangle(stale_bread, (60, 60), (196, 196), (140, 185, 215), -1)
    cv2.rectangle(stale_bread, (50, 50), (206, 65), (70, 120, 160), -1)
    
    oxidized_steak = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.ellipse(oxidized_steak, (128, 128), (85, 55), 15, 0, 360, (50, 60, 160), -1)
    cv2.ellipse(oxidized_steak, (120, 120), (24, 14), 10, 0, 360, (50, 75, 95), -1)

    nearly_group = [
        ("Spotted Banana (Sample)", banana_spotted, "Fruit"),
        ("Cut Apple (Moderate Browning)", cut_apple_brown, "Fruit"),
        ("Aged Banana (Sugar Spots)", aged_banana_skin, "Fruit"),
        ("Stale Bakery Loaf", stale_bread, "Bakery"),
        ("Oxidized Beef Steak", oxidized_steak, "Meat"),
    ]

    print(f"{'Image / Food Item':<32} | {'Spot %':<8} | {'Brown':<6} | {'Confidence':<12} | {'Final Label'}")
    print("-" * 75)
    for name, img, cat in nearly_group:
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img, category_hint=cat)
        pred = classifier.predict(img, category_hint=cat)
        print(f"{name:<32} | {metrics['spot_coverage_pct']:>6.2f}% | {metrics['browning_score']:>5.2f} | {pred['confidence']*100:>9.1f}% | {pred['freshness']}")
        assert pred['freshness'] == 'Nearly Spoiled', f"Failed for {name}: expected Nearly Spoiled, got {pred['freshness']}"

    print("\n-----------------------------------------------------------------")
    print("TEST 2B: GENUINELY SPOILED IMAGES (MUST STILL BE FLAGGED SPOILED)")
    print("-----------------------------------------------------------------")
    
    orange_spoiled = cv2.imread("static/samples/orange_spoiled.jpg")
    bread_spoiled = cv2.imread("static/samples/bread_spoiled.jpg")
    
    rotting_apple = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.circle(rotting_apple, (128, 128), 80, (40, 40, 180), -1)
    cv2.circle(rotting_apple, (130, 125), 45, (15, 15, 20), -1)
    
    moldy_tomato = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.circle(moldy_tomato, (128, 128), 75, (25, 30, 195), -1)
    cv2.circle(moldy_tomato, (115, 115), 25, (140, 155, 130), -1)
    cv2.circle(moldy_tomato, (140, 135), 20, (140, 155, 130), -1)
    
    spoiled_meat = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.ellipse(spoiled_meat, (128, 128), (85, 55), 15, 0, 360, (50, 95, 75), -1)

    spoiled_group = [
        ("Deteriorated Orange (Sample)", orange_spoiled, "Fruit"),
        ("Moldy Bread (Sample)", bread_spoiled, "Bakery"),
        ("Rotting Apple (Black Decay)", rotting_apple, "Fruit"),
        ("Moldy Tomato (Mycelium)", moldy_tomato, "Vegetable"),
        ("Spoiled Meat (Putrid Slime)", spoiled_meat, "Meat"),
    ]

    print(f"{'Image / Food Item':<32} | {'Spot %':<8} | {'Brown':<6} | {'Confidence':<12} | {'Final Label'}")
    print("-" * 75)
    for name, img, cat in spoiled_group:
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img, category_hint=cat)
        pred = classifier.predict(img, category_hint=cat)
        print(f"{name:<32} | {metrics['spot_coverage_pct']:>6.2f}% | {metrics['browning_score']:>5.2f} | {pred['confidence']*100:>9.1f}% | {pred['freshness']}")
        assert pred['freshness'] == 'Spoiled', f"Failed for {name}: expected Spoiled, got {pred['freshness']}"

    # =========================================================================
    # 3. GROUP 3: SHADOW + REAL LOCALIZED SPOILAGE COMBINATION
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("TEST 3: SHADOW / CURVE + REAL LOCALIZED SPOILAGE COMBINATION")
    print("-----------------------------------------------------------------")
    
    shadow_rot_orange = np.full((256, 256, 3), 245, dtype=np.uint8)
    for r in range(80, 0, -1):
        v_factor = 0.5 + (0.5 * (r / 80.0))
        color = (int(20 * v_factor), int(120 * v_factor), int(235 * v_factor))
        cv2.circle(shadow_rot_orange, (128, 128), r, color, -1)
    cv2.circle(shadow_rot_orange, (110, 90), 18, (10, 15, 25), -1)

    shadow_bruise_apple = apple_img.copy()
    shadow_bruise_apple[150:, :] = (shadow_bruise_apple[150:, :].astype(float) * 0.65).astype(np.uint8)
    cv2.circle(shadow_bruise_apple, (110, 95), 32, (15, 20, 25), -1)

    combo_group = [
        ("Shaded Orange + Real Rot Spot", shadow_rot_orange, "Fruit"),
        ("Shaded Apple + Real Bruise Spot", shadow_bruise_apple, "Fruit"),
    ]

    print(f"{'Image / Food Item':<34} | {'Spot %':<8} | {'Brown':<6} | {'Confidence':<12} | {'Final Label'}")
    print("-" * 77)
    for name, img, cat in combo_group:
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img, category_hint=cat)
        pred = classifier.predict(img, category_hint=cat)
        print(f"{name:<34} | {metrics['spot_coverage_pct']:>6.2f}% | {metrics['browning_score']:>5.2f} | {pred['confidence']*100:>9.1f}% | {pred['freshness']}")
        assert pred['freshness'] in ['Nearly Spoiled', 'Spoiled'], f"Failed to detect defect in {name}!"

    # =========================================================================
    # 4. GROUP 4: LIGHTING INVARIANCE TEST (BRIGHT VS DIM AMBIENT)
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("TEST 4: LIGHTING INVARIANCE (BRIGHT DIRECT LIGHT VS DIM AMBIENT)")
    print("-----------------------------------------------------------------")
    
    bright_apple = np.clip(apple_img.astype(float) * 1.25, 0, 255).astype(np.uint8)
    dim_apple = np.clip(apple_img.astype(float) * 0.65, 0, 255).astype(np.uint8)
    bright_tomato = np.clip(tomato_img.astype(float) * 1.25, 0, 255).astype(np.uint8)
    dim_tomato = np.clip(tomato_img.astype(float) * 0.65, 0, 255).astype(np.uint8)

    lighting_group = [
        ("Crisp Apple (Bright Studio)", bright_apple, "Fruit"),
        ("Crisp Apple (Dim Ambient)", dim_apple, "Fruit"),
        ("Vine Tomato (Bright Studio)", bright_tomato, "Vegetable"),
        ("Vine Tomato (Dim Ambient)", dim_tomato, "Vegetable"),
    ]

    print(f"{'Image / Lighting Variant':<32} | {'Spot %':<8} | {'Brown':<6} | {'Confidence':<12} | {'Final Label'}")
    print("-" * 75)
    for name, img, cat in lighting_group:
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img, category_hint=cat)
        pred = classifier.predict(img, category_hint=cat)
        print(f"{name:<32} | {metrics['spot_coverage_pct']:>6.2f}% | {metrics['browning_score']:>5.2f} | {pred['confidence']*100:>9.1f}% | {pred['freshness']}")
        assert pred['freshness'] == 'Fresh', f"Lighting invariance failed for {name}: got {pred['freshness']}"

    print("\n=================================================================")
    print("  ALL 4 COMPREHENSIVE VALIDATION SUITES PASSED 100%!             ")
    print("=================================================================")

if __name__ == "__main__":
    run_all_validation_tests()
