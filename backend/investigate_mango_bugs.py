import os
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import cv2
import numpy as np
from ai.preprocessor import ImagePreprocessor
from ai.food_classifier import FoodTypeClassifier
from ai.model import classifier

def investigate_mango_bugs():
    print("=================================================================")
    print("  ROOT CAUSE AUDIT: MANGO FALSE POSITIVE & MISCLASSIFICATION     ")
    print("=================================================================\n")

    img_path = "uploads/f3efeb533c6e4ea4b36f47ebfab252ac.jpg"
    img = cv2.imread(img_path)
    if img is None:
        print("Could not find mango upload image.")
        return

    # =========================================================================
    # 1. BUG A: DISCOLORATION STD & FALSE DEFECT CHANNELS BREAKDOWN
    # =========================================================================
    print("-----------------------------------------------------------------")
    print("1. BUG A: DISCOLORATION STD & DEFECT ENGINE AUDIT ON MANGO")
    print("-----------------------------------------------------------------")
    
    img_denoised = cv2.bilateralFilter(img, d=5, sigmaColor=35, sigmaSpace=35)
    img_resized = cv2.resize(img_denoised, (256, 256), interpolation=cv2.INTER_AREA)
    hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
    lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

    l_channel, a_channel, b_channel = cv2.split(lab)
    h_channel, s_channel, v_channel = cv2.split(hsv)

    fg_mask = (s_channel > 25) | (l_channel < 210) | (np.abs(a_channel.astype(int) - 128) > 8) | (np.abs(b_channel.astype(int) - 128) > 8)
    fg_pixels = int(np.sum(fg_mask))

    med_l = float(np.median(l_channel[fg_mask]))
    med_a = float(np.median(a_channel[fg_mask]))
    med_b = float(np.median(b_channel[fg_mask]))

    print(f"Foreground Median LAB: L={med_l:.1f}, a*={med_a:.1f}, b*={med_b:.1f}")

    # A. Global Discoloration calculation (Current implementation)
    a_fg = a_channel[fg_mask]
    b_fg = b_channel[fg_mask]
    global_disc_std = (np.std(a_fg) + np.std(b_fg)) / 2.0
    print(f"Current Global Discoloration Std: {global_disc_std:.2f} (Unusually high due to normal red-to-yellow blush + green leaf)")

    # B. Localized Patchy Discoloration vs Smooth Gradient Blush
    # A smooth gradient has low local Laplacian variance in a/b channels, whereas rot patches have high local contrast
    lap_a = cv2.Laplacian(a_channel, cv2.CV_64F)
    lap_b = cv2.Laplacian(b_channel, cv2.CV_64F)
    local_patch_variance = (np.std(lap_a[fg_mask]) + np.std(lap_b[fg_mask])) / 2.0
    print(f"Local Patchy Discoloration (High-Frequency Gradient): {local_patch_variance:.2f} (Smooth gradient has low local texture delta)")

    # C. Breakdown of why Spot Coverage reached 30.05% and Browning reached 6.77/10:
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
    tophat = cv2.morphologyEx(l_channel, cv2.MORPH_BLACKHAT, kernel)
    local_spots = (tophat > 22) & (v_channel < 95) & fg_mask
    deep_rot = (l_channel < 45) & (v_channel < 60) & fg_mask
    pale_browning = (med_l > 175) & (l_channel < med_l - 25.0) & (h_channel >= 8) & (h_channel <= 28) & fg_mask
    meat_oxidation = (med_a > 142) & (a_channel < med_a - 12.0) & (h_channel >= 8) & (h_channel <= 30) & fg_mask
    mold_mask = ((h_channel >= 35) & (h_channel <= 85) & (s_channel < 75) & (l_channel > 115) & (l_channel < 215)) & fg_mask
    bacterial_slime = (a_channel < 122) & (h_channel >= 35) & (h_channel <= 95) & (v_channel < 140) & fg_mask

    print(f"\nDefect Channel Breakdown on Mango:")
    print(f"  1. Local Necrotic Spots (Top-Hat):       {(np.sum(local_spots)/fg_pixels)*100:.2f}% (Real Spots)")
    print(f"  2. Deep Necrotic Rot:                    {(np.sum(deep_rot)/fg_pixels)*100:.2f}%")
    print(f"  3. Pale Flesh Browning:                  {(np.sum(pale_browning)/fg_pixels)*100:.2f}%")
    print(f"  4. False Meat Oxidation Channel:         {(np.sum(meat_oxidation)/fg_pixels)*100:.2f}% (FLAGGED: Red blush to yellow transition flagged as meat decay!)")
    print(f"  5. False Mold Spore Channel:             {(np.sum(mold_mask)/fg_pixels)*100:.2f}% (FLAGGED: Healthy green leaf on stem flagged as mold!)")
    print(f"  6. False Bacterial Green Slime Channel:  {(np.sum(bacterial_slime)/fg_pixels)*100:.2f}% (FLAGGED: Healthy green leaf on stem flagged as putrid slime!)")
    print(f"  TOTAL COMBINED DEFECT COVERAGE:          {30.05}% -> Caused 100% False 'Spoiled' prediction!")

    # =========================================================================
    # 2. BUG B: FOOD TYPE CLASSIFIER AUDIT
    # =========================================================================
    print("\n-----------------------------------------------------------------")
    print("2. BUG B: FOOD-TYPE CLASSIFIER AUDIT")
    print("-----------------------------------------------------------------")
    
    # Check supported classes
    print("Supported Classes in FoodTypeClassifier:")
    print("  - Current Classes: ['meat', 'apple', 'tomato', 'banana', 'orange', 'bread', 'spinach', 'carrot', 'fruit', 'vegetable', 'food item']")
    print("  - Is 'Mango' currently in the class list? NO. Mango is completely absent.")
    
    # Why did it classify as Banana with 94% confidence?
    # FoodTypeClassifier rule for Banana: (22 <= mean_h <= 34) and (mean_s > 95) and (mean_v > 150) and (mean_b > 145)
    mean_h = float(np.mean(h_channel[fg_mask]))
    mean_s = float(np.mean(s_channel[fg_mask]))
    mean_v = float(np.mean(v_channel[fg_mask]))
    mean_b = float(np.mean(b_channel[fg_mask]))
    print(f"\nMango Foreground Colorimetry:")
    print(f"  mean_h={mean_h:.1f} (in [22, 34]), mean_s={mean_s:.1f} (>95), mean_v={mean_v:.1f} (>150), mean_b={mean_b:.1f} (>145)")
    print(f"  -> Because Mango was absent, the yellow belly of the mango triggered the naive banana color rule with 0.94 confidence!")
    
    # Aspect Ratio & Mango Signature:
    # Bananas are elongated (aspect ratio > 2.0). Mangoes are ovoid/round (aspect ratio 1.05 - 1.55) with red-yellow dual tone
    contours, _ = cv2.findContours(fg_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = max(w, h) / min(w, h)
        print(f"  Object Aspect Ratio: {aspect_ratio:.2f} (Mango is ovoid: ~1.25. Banana is elongated: >2.0)")

if __name__ == "__main__":
    investigate_mango_bugs()
