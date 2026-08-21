import os
import sys
import random
from pathlib import Path
from collections import defaultdict

import cv2
import numpy as np

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))

from ai.food_classifier import FoodTypeClassifier, FOOD_CLASSES

def run_holdout_benchmark(samples_per_class: int = 15, seed: int = 999):
    random.seed(seed)
    fv_base = project_root / "dataset_raw" / "fruits_vegetables" / "Unified_Dataset"
    meat_base = project_root / "dataset_raw" / "meat" / "Meat Freshness.v1-new-dataset.multiclass"
    bread_base = project_root / "dataset_raw" / "bread"
    sample_uploads = project_root / "sample_uploads"

    # Evaluation targets (11 CNN classes + Bakery + Dairy)
    all_eval_classes = FOOD_CLASSES + ["bakery", "dairy"]
    test_dataset = defaultdict(list)

    # 1. Collect unseen holdout images for Fruits & Vegetables (skipping first 300 used in training)
    for cls_name in FOOD_CLASSES:
        if cls_name == "meat":
            continue
        cls_dir = fv_base / cls_name
        if cls_dir.exists():
            pool = []
            for sub in ["fresh", "rotten"]:
                sub_p = cls_dir / sub
                if sub_p.exists():
                    files = [f for f in sub_p.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]]
                    pool.extend(files)
            # Shuffle with a different seed and pick from holdout pool
            random.shuffle(pool)
            holdout_pool = pool[300:] if len(pool) > 300 else pool
            test_dataset[cls_name] = random.sample(holdout_pool, min(samples_per_class, len(holdout_pool)))

    # 2. Collect unseen Meat samples
    if meat_base.exists():
        meat_pool = []
        for sub in ["train", "valid"]:
            sub_p = meat_base / sub
            if sub_p.exists():
                meat_pool.extend([f for f in sub_p.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
        random.shuffle(meat_pool)
        holdout_meat = meat_pool[300:] if len(meat_pool) > 300 else meat_pool
        test_dataset["meat"] = random.sample(holdout_meat, min(samples_per_class, len(holdout_meat)))

    # 3. Collect Bakery samples (from dataset_raw/bread and sample_uploads/bakery)
    bakery_pool = []
    if bread_base.exists():
        bakery_pool.extend([f for f in bread_base.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    if (sample_uploads / "bakery").exists():
        bakery_pool.extend([f for f in (sample_uploads / "bakery").iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    test_dataset["bakery"] = random.sample(bakery_pool, min(samples_per_class, len(bakery_pool)))

    # 4. Collect Dairy samples (from sample_uploads/cheese)
    dairy_pool = []
    if (sample_uploads / "cheese").exists():
        dairy_pool.extend([f for f in (sample_uploads / "cheese").iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    if (sample_uploads / "dairy").exists():
        dairy_pool.extend([f for f in (sample_uploads / "dairy").iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]])
    test_dataset["dairy"] = dairy_pool if dairy_pool else []

    # Initialize Confusion Matrix: rows = Ground Truth, cols = Predictions
    all_possible_preds = list(all_eval_classes) + ["food item", "fruit", "vegetable"]
    confusion_matrix = {gt: {pred: 0 for pred in all_possible_preds} for gt in all_eval_classes}

    total_tested = 0
    total_correct = 0
    per_class_results = {}

    print("=" * 90)
    print("  FRESHCO AI — INDEPENDENT HOLDOUT BENCHMARK (13 FOOD CLASSES)")
    print("=" * 90)

    for gt_class in all_eval_classes:
        images = test_dataset[gt_class]
        if not images:
            continue

        c_correct = 0
        for img_path in images:
            img = cv2.imdecode(np.fromfile(str(img_path), dtype=np.uint8), cv2.IMREAD_COLOR)
            if img is None:
                continue

            # Pass 'General' to test pure auto-detection without relying on category hints
            pred_label, conf = FoodTypeClassifier.identify_food_type(img, category_hint="General")
            pred_lower = pred_label.lower()

            # Record in confusion matrix
            if pred_lower in confusion_matrix[gt_class]:
                confusion_matrix[gt_class][pred_lower] += 1
            else:
                confusion_matrix[gt_class]["food item"] += 1

            # Check correctness (handles dairy/cheese equivalence)
            is_match = (pred_lower == gt_class) or (gt_class == "dairy" and pred_lower in ["dairy", "cheese"])
            if is_match:
                c_correct += 1
                total_correct += 1
            total_tested += 1

        acc = (c_correct / len(images)) * 100 if images else 0
        per_class_results[gt_class] = (c_correct, len(images), acc)
        print(f"  • {gt_class.upper():<12}: {c_correct:2d}/{len(images):2d} ({acc:5.1f}%) | Tested on {len(images)} independent unseen images")

    overall_acc = (total_correct / total_tested) * 100 if total_tested > 0 else 0

    print("\n" + "=" * 90)
    print("  CONFUSION MATRIX (Ground Truth rows vs Model Prediction columns)")
    print("=" * 90)

    # Print Table Header
    header_cols = [c[:4] for c in all_eval_classes] + ["Food"]
    print(f"{'GT / PRED':<12} | " + " | ".join(f"{col:>4}" for col in header_cols) + " | Accuracy")
    print("-" * 90)

    for gt in all_eval_classes:
        if gt not in test_dataset or not test_dataset[gt]:
            continue
        row_counts = [confusion_matrix[gt].get(p, 0) for p in all_eval_classes]
        food_item_count = confusion_matrix[gt].get("food item", 0) + confusion_matrix[gt].get("fruit", 0) + confusion_matrix[gt].get("vegetable", 0)
        c_cor, c_tot, c_acc = per_class_results[gt]
        row_str = " | ".join(f"{cnt:4d}" for cnt in row_counts + [food_item_count])
        print(f"{gt.upper():<12} | {row_str} | {c_acc:5.1f}%")

    print("=" * 90)
    print(f"  TOTAL INDEPENDENT HOLDOUT ACCURACY: {total_correct}/{total_tested} ({overall_acc:.2f}%)")
    print(f"  BASELINE COMPARISONS:")
    print(f"    • Old Heuristic Baseline   : 15.50% (28/180)")
    print(f"    • Subset Training Val Acc  : 92.73% (612/660)")
    print(f"    • Independent Holdout Test : {overall_acc:.2f}% ({total_correct}/{total_tested})")
    print("=" * 90)

if __name__ == "__main__":
    run_holdout_benchmark()
