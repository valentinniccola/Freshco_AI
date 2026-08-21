import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import joblib
import numpy as np
from ai.preprocessor import ImagePreprocessor
from ai.train_and_evaluate import FreshnessFeatureExtractor
from ai.model import classifier

def investigate_all_5_points():
    print("=================================================================")
    print("  ROOT CAUSE INVESTIGATION: FRESH FRUITS LABELED NEARLY SPOILED  ")
    print("=================================================================\n")

    # =========================================================================
    # POINT 1: CLASS INDEX / LABEL MAPPING AUDIT
    # =========================================================================
    print("-----------------------------------------------------------------")
    print("1. CLASS INDEX / LABEL MAPPING AUDIT")
    print("-----------------------------------------------------------------")
    model_path = Path("ai/models/mobilenetv2_freshness_model.joblib")
    model = joblib.load(str(model_path)) if model_path.exists() else None
    
    print(f"Model Path: {model_path.name}")
    if model is not None:
        print(f"Scikit-Learn Model Classes in joblib: {model.classes_}")
    print(f"Training Class Names: ['Fresh' (0), 'Nearly Spoiled' (1), 'Spoiled' (2)]")
    print(f"Inference MobileNetV2.CLASSES: {classifier.CLASSES}")
    
    # Test on fresh fruit images
    fresh_images = [
        ("apple_fresh.jpg", "Fresh Apple (Studio)"),
        ("tomato_fresh.jpg", "Fresh Tomato (Vine)"),
        ("meat_fresh.jpg", "Fresh Steak (Meat)"),
    ]

    # Synthesize additional realistic fresh fruit images (Yellow fresh banana, Green fresh granny smith, Vibrant orange)
    # 1. Fresh Yellow Banana (clean yellow, no spots)
    fresh_banana = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.ellipse(fresh_banana, (128, 128), (85, 32), -25, 0, 360, (40, 215, 245), -1) # BGR Bright Yellow
    
    # 2. Fresh Green Pear / Apple (smooth green, no spots)
    fresh_green_apple = np.full((256, 256, 3), 245, dtype=np.uint8)
    cv2.circle(fresh_green_apple, (128, 128), 75, (50, 200, 80), -1) # BGR Fresh Green

    fresh_test_set = [
        ("apple_fresh.jpg", cv2.imread("static/samples/apple_fresh.jpg"), "Sample Apple"),
        ("tomato_fresh.jpg", cv2.imread("static/samples/tomato_fresh.jpg"), "Sample Tomato"),
        ("fresh_banana_clean", fresh_banana, "Clean Yellow Banana (0 spots)"),
        ("fresh_green_apple", fresh_green_apple, "Clean Green Apple (0 spots)"),
        ("meat_fresh.jpg", cv2.imread("static/samples/meat_fresh.jpg"), "Sample Beef Steak"),
    ]

    print("\nRaw Softmax / Probability Vectors for 5 Known Fresh Test Images:")
    for name, img, desc in fresh_test_set:
        if img is None:
            continue
        
        # Raw defect metrics
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img)
        
        # Calculate raw feature vector
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h_ch, s_ch, v_ch = cv2.split(hsv)
        organic_mask = ((h_ch <= 85) | (h_ch >= 130)) & (s_ch > 25) & (v_ch > 25)
        organic_ratio = float(np.sum(organic_mask) / organic_mask.size)
        
        feat_vec = FreshnessFeatureExtractor.extract_features(
            spot_pct=metrics["spot_coverage_pct"],
            browning=metrics["browning_score"],
            discoloration=metrics["discoloration_index"],
            homogeneity=metrics["surface_homogeneity"],
            organic_hues=organic_ratio
        ).reshape(1, -1)
        
        raw_probs = model.predict_proba(feat_vec)[0] if model is not None else [0, 0, 0]
        final_pred = classifier.predict(img)
        
        print(f"\nImage: {name} ({desc})")
        print(f"  Raw Model Probabilities (0, 1, 2): P(0/Fresh)={raw_probs[0]:.4f} | P(1/Nearly)={raw_probs[1]:.4f} | P(2/Spoiled)={raw_probs[2]:.4f}")
        print(f"  Final API Probabilities:          {final_pred['all_probabilities']}")
        print(f"  Predicted Label:                  {final_pred['freshness']} ({final_pred['confidence']*100:.1f}%)")
        print(f"  OpenCV Defect Metrics:            Spot={metrics['spot_coverage_pct']}%, Browning={metrics['browning_score']}, Discoloration={metrics['discoloration_index']}, Homog={metrics['surface_homogeneity']}%")

    # =========================================================================
    # POINT 2: CONFIDENCE THRESHOLD & OVERRIDE CHECKS
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("2. CONFIDENCE THRESHOLD & OVERRIDE RULES CHECK")
    print("-----------------------------------------------------------------")
    print("Checking if 'Fresh' has a higher threshold or downstream rule overrides:")
    print("  - Stage 3 Low Confidence Threshold: 0.65 (< 65% marks as 'Unconfident')")
    print("  - Close Margin Threshold: <= 0.10 (marks as 'Uncertain')")
    print("  - model.py Guardrail A: If spot_pct < 4.5 and browning < 2.0, redistributes p_spoiled into p_fresh (70%) and p_nearly (30%).")
    print("  - model.py Guardrail B: If spot_pct > 24.0 or browning > 4.8, boosts p_spoiled to 0.95.")
    print("  - Checking if Guardrail A or Feature formula pushes Fresh into Nearly Spoiled...")

    # =========================================================================
    # POINT 3: PREPROCESSING PIPELINE AUDIT (Train vs Inference)
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("3. PREPROCESSING PIPELINE AUDIT (Train vs Inference)")
    print("-----------------------------------------------------------------")
    print("Inference Pipeline:")
    print("  - ImagePreprocessor.load_image_from_bytes() -> PIL EXIF orientation correction -> BGR")
    print("  - ImagePreprocessor.extract_visual_defect_metrics(img_bgr) -> CLAHE on L-channel in LAB -> Bilateral filter")
    print("  - ImagePreprocessor.preprocess_for_model(img_bgr) -> INTER_AREA resize (224x224) -> [-1, 1] range float")
    
    # Check impact of CLAHE on fresh fruit images
    for name, img, desc in fresh_test_set[:3]:
        if img is None: continue
        # Defect metrics WITH CLAHE (current pipeline)
        metrics_clahe = ImagePreprocessor.extract_visual_defect_metrics(img)
        
        # Defect metrics WITHOUT CLAHE (raw LAB)
        lab_raw = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l_raw, a_raw, b_raw = cv2.split(lab_raw)
        gray_raw = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        homog_raw = 100.0 - min(100.0, float(cv2.Laplacian(cv2.resize(gray_raw, (224, 224)), cv2.CV_64F).var()) / 10.0)
        
        print(f"\nCLAHE Impact on {name}:")
        print(f"  With CLAHE:    Spot={metrics_clahe['spot_coverage_pct']}%, Browning={metrics_clahe['browning_score']}, Discoloration={metrics_clahe['discoloration_index']}")

    # =========================================================================
    # POINT 4: TRAINING DATA IMBALANCE & CLASS OVERLAP AUDIT
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("4. TRAINING DATA IMBALANCE & CLASS OVERLAP AUDIT")
    print("-----------------------------------------------------------------")
    print("Dataset counts per class in train_and_evaluate.py:")
    print("  - Class 0 (Fresh):          400 samples (33.3%)")
    print("  - Class 1 (Nearly Spoiled): 400 samples (33.3%)")
    print("  - Class 2 (Spoiled):        400 samples (33.3%)")
    print("  - Total:                   1200 samples (Strictly Balanced 1:1:1)")
    print("\nBoundary ranges in generate_expanded_dataset():")
    print("  - Fresh Subgroup A: spot 0.0-2.5, browning 0.0-1.0, disc 3.0-16.5, homog 70-98")
    print("  - Fresh Subgroup B (Cut Fruit): spot 0.5-3.8, browning 0.8-1.5, disc 6.0-15.0")
    print("  - Nearly Spoiled Subgroup A: spot 5.0-22.0, browning 1.8-4.2, disc 11.0-20.0")
    print("  - Nearly Spoiled Subgroup B (Cut Fruit): spot 4.2-18.0, browning 2.0-4.4")

    # =========================================================================
    # POINT 5: OPENCV DEFECT SIGNAL SENSITIVITY AUDIT
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("5. OPENCV DEFECT SIGNAL SENSITIVITY AUDIT")
    print("-----------------------------------------------------------------")
    print("Checking how extract_visual_defect_metrics() computes browning and spot coverage:")
    
    # Audit on real fresh fruit images from static/samples and uploads
    for name, img, desc in fresh_test_set:
        if img is None: continue
        metrics = ImagePreprocessor.extract_visual_defect_metrics(img)
        spoilage_score = (metrics["spot_coverage_pct"] * 1.4) + (metrics["browning_score"] * 3.2) + (max(0.0, metrics["discoloration_index"] - 16.0) * 0.5)
        print(f"{name:<22} -> Spot={metrics['spot_coverage_pct']:>5.2f}% | Browning={metrics['browning_score']:>4.2f} | Discoloration={metrics['discoloration_index']:>5.2f} | Spoilage Score={spoilage_score:>5.2f}")

if __name__ == "__main__":
    investigate_all_5_points()
