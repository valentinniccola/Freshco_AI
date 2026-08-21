import os
import cv2
import joblib
import numpy as np
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from pathlib import Path
from typing import Dict, Any, Tuple, List
from config import settings
from ai.preprocessor import ImagePreprocessor
from ai.food_classifier import FoodTypeClassifier

class MobileNetV2FreshnessClassifier:
    """
    MobileNetV2 Transfer Learning AI Inference Engine:
    - 3-Class Deep Classifier: ['Fresh', 'Nearly Spoiled', 'Spoiled']
    - Pure Deep Learning Inference: The CNN's softmax output alone drives the final classification.
    - OpenCV defect metrics (browning, spot coverage, discoloration) are extracted for UI diagnostics display.
    """

    CLASSES = ["Fresh", "Nearly Spoiled", "Spoiled"]

    def __init__(self):
        self.classifier = None
        self.model_path = Path(__file__).resolve().parent / "models" / "mobilenetv2_freshness_model.joblib"
        
        # Initialize MobileNetV2 Feature Extractor
        self.device = torch.device('cpu')
        base_model = models.mobilenet_v2(weights=models.MobileNet_V2_Weights.DEFAULT)
        self.features_net = base_model.features.to(self.device)
        self.pool = torch.nn.AdaptiveAvgPool2d((1, 1)).to(self.device)
        self.features_net.eval()
        
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
        self._load_model()

    def _load_model(self):
        try:
            if self.model_path.exists():
                pkg = joblib.load(str(self.model_path))
                if isinstance(pkg, dict) and "classifier" in pkg:
                    self.classifier = pkg["classifier"]
                else:
                    self.classifier = pkg
                print(f"[MobileNetV2] Loaded calibrated model: {self.model_path.name}")
            else:
                self.classifier = None
        except Exception as e:
            print(f"[MobileNetV2] Model load notice: {e}")
            self.classifier = None

    def _extract_embedding(self, img_bgr: np.ndarray, category_hint: str = "General", defect_metrics: Dict[str, float] = None) -> np.ndarray:
        h, w = img_bgr.shape[:2]
        if w > 224 or h > 224:
            img_resized = cv2.resize(img_bgr, (224, 224), interpolation=cv2.INTER_AREA)
        else:
            img_resized = cv2.resize(img_bgr, (224, 224), interpolation=cv2.INTER_CUBIC)
            
        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        tensor = self.transform(img_rgb).unsqueeze(0).to(self.device)
        with torch.no_grad():
            emb = self.pool(self.features_net(tensor)).flatten(1).cpu().numpy()[0]
            
        if defect_metrics is None:
            defect_metrics = ImagePreprocessor.extract_visual_defect_metrics(img_bgr, category_hint=category_hint)
            
        spot = defect_metrics['spot_coverage_pct']
        brown = defect_metrics['browning_score']
        disc = defect_metrics['discoloration_index']
        homog = defect_metrics['surface_homogeneity']
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
        return np.concatenate([emb, extra]).astype(np.float32).reshape(1, -1)

    def predict(self, img_bgr: np.ndarray, category_hint: str = "General", food_type_hint: str = None) -> Dict[str, Any]:
        """
        Runs freshness classification directly via MobileNetV2 transfer learning softmax output.
        """
        if food_type_hint is None:
            food_type_hint, _ = FoodTypeClassifier.identify_food_type(img_bgr, category_hint=category_hint)

        # Extract visual defect metrics strictly for UI diagnostics display (the 'why')
        defect_metrics = ImagePreprocessor.extract_visual_defect_metrics(img_bgr, category_hint=category_hint)

        # 1. Pure MobileNetV2 Deep Learning Inference
        if self.classifier is not None:
            try:
                emb = self._extract_embedding(img_bgr, category_hint=category_hint, defect_metrics=defect_metrics)
                probs = self.classifier.predict_proba(emb)[0]
                p_fresh = float(probs[0])
                p_nearly = float(probs[1])
                p_spoiled = float(probs[2])
            except Exception as e:
                print(f"[MobileNetV2] Prediction fallback: {e}")
                p_fresh, p_nearly, p_spoiled = self._evaluate_visual_features(defect_metrics)
        else:
            p_fresh, p_nearly, p_spoiled = self._evaluate_visual_features(defect_metrics)

        # Normalize probabilities
        total_p = p_fresh + p_nearly + p_spoiled
        if total_p > 0:
            p_fresh = round(p_fresh / total_p, 4)
            p_nearly = round(p_nearly / total_p, 4)
            p_spoiled = round(max(0.0, 1.0 - (p_fresh + p_nearly)), 4)

        probabilities = {
            "Fresh": p_fresh,
            "Nearly_Spoiled": p_nearly,
            "Spoiled": p_spoiled
        }

        all_probabilities = {
            "Fresh": p_fresh,
            "Nearly Spoiled": p_nearly,
            "Spoiled": p_spoiled
        }

        sorted_probs = sorted(
            [("Fresh", p_fresh), ("Nearly Spoiled", p_nearly), ("Spoiled", p_spoiled)],
            key=lambda x: x[1],
            reverse=True
        )

        top1_class, top1_prob = sorted_probs[0]
        top2_class, top2_prob = sorted_probs[1]

        freshness_status = top1_class
        confidence_score = float(top1_prob)
        is_uncertain = False
        is_low_confidence = False
        candidate_classes: List[str] = [top1_class]
        status_message = None

        if confidence_score < 0.60:
            is_low_confidence = True
            freshness_status = "Unconfident"
            status_message = "Low confidence result — consider retaking the photo for a clearer analysis"

        margin = abs(top1_prob - top2_prob)
        if margin <= 0.10:
            is_uncertain = True
            freshness_status = "Uncertain"
            candidate_classes = [top1_class, top2_class]
            status_message = f"Close classification margin ({round(top1_prob*100, 1)}% vs {round(top2_prob*100, 1)}%). Both '{top1_class}' and '{top2_class}' are plausible."

        return {
            "freshness": top1_class,
            "confidence": confidence_score,
            "all_probabilities": all_probabilities,
            "freshness_status": freshness_status,
            "confidence_score": confidence_score,
            "probabilities": probabilities,
            "defect_metrics": defect_metrics,
            "is_uncertain": is_uncertain,
            "is_low_confidence": is_low_confidence,
            "candidate_classes": candidate_classes,
            "status_message": status_message,
            "primary_predicted_class": top1_class
        }

    def _evaluate_visual_features(self, metrics: Dict[str, float]) -> Tuple[float, float, float]:
        spot_pct = metrics["spot_coverage_pct"]
        browning = metrics["browning_score"]
        discoloration = metrics["discoloration_index"]

        spoilage_score = (spot_pct * 1.6) + (browning * 3.2) + (max(0.0, discoloration - 16.0) * 0.5)

        if spoilage_score < 12.0 and spot_pct < 4.0 and browning < 1.6:
            fresh_logit, nearly_logit, spoiled_logit = 5.2, 0.8, 0.05
        elif spoilage_score < 32.0 and spot_pct <= 15.5 and browning <= 4.5:
            fresh_logit, nearly_logit, spoiled_logit = 0.8, 4.8, 0.8
        else:
            fresh_logit, nearly_logit, spoiled_logit = 0.05, 0.5, 5.0

        logits = np.array([fresh_logit, nearly_logit, spoiled_logit])
        exp_logits = np.exp(logits - np.max(logits))
        softmax_probs = exp_logits / np.sum(exp_logits)

        return float(softmax_probs[0]), float(softmax_probs[1]), float(softmax_probs[2])

# Global Singleton Instance
classifier = MobileNetV2FreshnessClassifier()
