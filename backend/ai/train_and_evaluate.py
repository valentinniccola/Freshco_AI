import os
import sys
import time
import joblib
import cv2
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

import torch
import torchvision.models as models
import torchvision.transforms as transforms

# Set seed for reproducibility
np.random.seed(42)
torch.manual_seed(42)

root_dir = Path(__file__).resolve().parent.parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai.preprocessor import ImagePreprocessor

dataset_dir = root_dir / "dataset"
model_dir = backend_dir / "ai" / "models"
model_dir.mkdir(parents=True, exist_ok=True)

class MobileNetV2HybridExtractor:
    """
    Unified MobileNetV2 Transfer Learning Feature Extractor:
    - 1,280 Deep visual features from pretrained MobileNetV2
    - Multi-scale surface texture, defect density & chromatic metrics
    - Total representation length: 1,292 dimensions
    """
    def __init__(self, device='cpu'):
        self.device = torch.device(device)
        base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        self.features_net = base_model.features.to(self.device)
        self.pool = torch.nn.AdaptiveAvgPool2d((1, 1)).to(self.device)
        self.features_net.eval()
        
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def extract(self, img_bgr: np.ndarray, category_hint: str = "General") -> np.ndarray:
        h, w = img_bgr.shape[:2]
        img_resized = cv2.resize(img_bgr, (224, 224), interpolation=cv2.INTER_AREA if (w > 224 or h > 224) else cv2.INTER_CUBIC)
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        tensor = self.transform(img_rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.pool(self.features_net(tensor)).flatten(1).cpu().numpy()[0]
            
        m = ImagePreprocessor.extract_visual_defect_metrics(img_bgr, category_hint=category_hint)
        spot = m['spot_coverage_pct']
        brown = m['browning_score']
        disc = m['discoloration_index']
        homog = m['surface_homogeneity']
        spoilage = (spot * 1.6) + (brown * 3.2)
        
        extra = [
            spot, brown, disc, homog, spoilage,
            spot / (homog + 10.0),
            (spot * brown) / 10.0,
            np.log1p(spot),
            np.log1p(brown),
            1.0 if (spot < 4.0 and brown < 1.6) else 0.0,
            1.0 if (4.0 <= spot < 16.0 and brown < 4.0) else 0.0,
            1.0 if (spot >= 16.0 or brown >= 4.0) else 0.0
        ]
        return np.concatenate([emb, extra]).astype(np.float32)

def safe_imread(path_str):
    try:
        data = np.fromfile(path_str, dtype=np.uint8)
        if len(data) == 0:
            return None
        return cv2.imdecode(data, cv2.IMREAD_COLOR)
    except Exception:
        return None

def build_training_dataset(samples_per_class=2500):
    print(f"Collecting balanced dataset samples ({samples_per_class} per class)...")
    extractor = MobileNetV2HybridExtractor()
    
    class_paths = {0: [], 1: [], 2: []}
    tier_map = {'fresh': 0, 'nearly_spoiled': 1, 'spoiled': 2}
    
    for cat in ['fruits_vegetables', 'meat']:
        for tier_name, label in tier_map.items():
            p = dataset_dir / cat / tier_name
            if p.exists():
                files = [f for f in p.glob('*') if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']]
                class_paths[label].extend([(f, cat) for f in files])
                print(f"  Found {len(files)} in {cat}/{tier_name}")
                
    X = []
    y = []
    
    for label in [0, 1, 2]:
        all_items = class_paths[label]
        np.random.shuffle(all_items)
        selected = all_items[:samples_per_class]
        print(f"Extracting features for Class {label} ({len(selected)} images)...")
        
        t0 = time.time()
        for idx, (f, cat) in enumerate(selected):
            img = safe_imread(str(f))
            if img is None:
                continue
            feat = extractor.extract(img, category_hint='Meat' if cat == 'meat' else 'Fruit')
            X.append(feat)
            y.append(label)
            if (idx + 1) % 500 == 0 or (idx + 1) == len(selected):
                elapsed = time.time() - t0
                print(f"  Processed {idx + 1}/{len(selected)} in {elapsed:.1f}s")
                
    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)

def train_and_evaluate_model():
    print("=" * 70)
    print("  FRESHCO AI: MOBILENETV2 TRANSFER LEARNING TRAINING & EVALUATION  ")
    print("=" * 70)
    
    X, y = build_training_dataset(samples_per_class=2500)
    print(f"\nTotal Dataset: {len(X)} samples, Feature Dimension: {X.shape[1]}")
    
    # 80% Train, 20% Test Split (Stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Train Set: {len(X_train)} samples | Test Set: {len(X_test)} samples")
    
    # Class weights prioritizing Recall on Spoiled (Class 2)
    raw_weights = compute_class_weight(class_weight='balanced', classes=np.unique(y_train), y=y_train)
    raw_weights[2] *= 1.25 # Prioritize recall on spoiled food
    class_weight_dict = {0: raw_weights[0], 1: raw_weights[1], 2: raw_weights[2]}
    print(f"Calculated Class Weights (Prioritizing Spoiled Recall): {class_weight_dict}")
    
    print("\nTraining Standardized Deep Neural Classification Pipeline...")
    t0 = time.time()
    
    pipeline = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(256, 128),
            activation='relu',
            solver='adam',
            alpha=1e-4,
            learning_rate_init=1e-3,
            max_iter=200,
            early_stopping=True,
            n_iter_no_change=15,
            random_state=42
        )
    )
    
    pipeline.fit(X_train, y_train)
    print(f"Model Training Complete in {time.time() - t0:.1f}s")
    
    # Evaluate on held-out test set
    y_pred = pipeline.predict(X_test)
    class_names = ["Fresh", "Nearly Spoiled", "Spoiled"]
    
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2])
    print("\n" + "=" * 70)
    print(f"  TEST SET EVALUATION RESULTS (N = {len(y_test)} held-out images)  ")
    print("=" * 70)
    print("\nConfusion Matrix (Rows: Ground Truth, Columns: Prediction):")
    print(f"{'':>22} | {'Pred: Fresh':>13} | {'Pred: Nearly':>13} | {'Pred: Spoiled':>13}")
    print("-" * 70)
    print(f"{'Actual: Fresh':>22} | {cm[0, 0]:>13} | {cm[0, 1]:>13} | {cm[0, 2]:>13}")
    print(f"{'Actual: Nearly Spoiled':>22} | {cm[1, 0]:>13} | {cm[1, 1]:>13} | {cm[1, 2]:>13}")
    print(f"{'Actual: Spoiled':>22} | {cm[2, 0]:>13} | {cm[2, 1]:>13} | {cm[2, 2]:>13}")
    
    report = classification_report(y_test, y_pred, target_names=class_names, digits=4)
    print("\nClassification Report (Precision, Recall, F1-Score):")
    print(report)
    
    # Save the trained model artifact
    save_path = model_dir / "mobilenetv2_freshness_model.joblib"
    model_package = {
        "classifier": pipeline,
        "class_names": class_names,
        "embedding_dim": 1292,
        "trained_date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    joblib.dump(model_package, save_path)
    print(f"\n[Artifact Saved] Successfully saved MobileNetV2 model package to: {save_path.name}")

if __name__ == '__main__':
    train_and_evaluate_model()
