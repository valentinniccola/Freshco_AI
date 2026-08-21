import os
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
import torch
import torch.nn as nn
import torchvision.transforms as transforms
import torchvision.models as models
from PIL import Image

FOOD_CLASSES = [
    "apple",
    "banana",
    "bellpepper",
    "carrot",
    "cucumber",
    "mango",
    "meat",
    "orange",
    "potato",
    "strawberry",
    "tomato",
    "bakery",
]

class FoodTypeClassifier:
    """
    Trained MobileNetV2 Food-Type Classification Engine:
    Classifies specific fruits, vegetables, meat, and bakery items using a dedicated PyTorch MobileNetV2 CNN.
    Includes defensive category fallback routing for Dairy and Food Items.
    """
    _model = None
    _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    _transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    @classmethod
    def _get_model(cls):
        if cls._model is None:
            model_path = Path(__file__).resolve().parent / "models" / "mobilenetv2_food_type_cnn.pt"
            weights = models.MobileNet_V2_Weights.DEFAULT
            model = models.mobilenet_v2(weights=weights)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(
                nn.Dropout(p=0.2),
                nn.Linear(in_features, len(FOOD_CLASSES))
            )
            
            if model_path.exists():
                checkpoint = torch.load(str(model_path), map_location=cls._device, weights_only=True)
                if "model_state_dict" in checkpoint:
                    model.load_state_dict(checkpoint["model_state_dict"])
                else:
                    model.load_state_dict(checkpoint)
            
            model = model.to(cls._device)
            model.eval()
            cls._model = model
            
        return cls._model

    @classmethod
    def identify_food_type(cls, img_bgr: np.ndarray, category_hint: str = None) -> Tuple[str, float]:
        """
        Identifies food type:
        1. Honors explicit user category hints (Bakery, Dairy, Meat, Fruit, Vegetable).
        2. In auto-detect mode, runs MobileNetV2 CNN inference across 12 trained classes.
        3. If CNN confidence is < 65%, uses safe defensive routing to Bakery / Dairy / Food Item.
        """
        # 1. Explicit Category Intent Handling
        if category_hint:
            hint_lower = category_hint.strip().lower()
            if hint_lower in ["bakery", "bread"]:
                return "bakery", 0.90
            elif hint_lower in ["dairy", "cheese", "milk"]:
                return "dairy", 0.90
            elif hint_lower == "meat":
                return "meat", 0.92

        # 2. Run Trained MobileNetV2 CNN Model
        try:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            tensor = cls._transform(pil_img).unsqueeze(0).to(cls._device)

            model = cls._get_model()
            with torch.no_grad():
                logits = model(tensor)
                probs = torch.nn.functional.softmax(logits[0], dim=0)
                top_prob, top_idx = torch.max(probs, dim=0)
                top_conf = float(top_prob.item())
                top_class = FOOD_CLASSES[top_idx.item()]

            # 3. High-Confidence Detection: Return specific food name (or bakery)
            if top_conf >= 0.65:
                return top_class, top_conf

        except Exception as e:
            top_class = None
            top_conf = 0.0

        # 4. Safe Defensive Routing (When CNN confidence is low / uncertain)
        # NEVER output a specific fruit/veg name here — strictly route to Bakery, Dairy, or Food Item.
        h, w, _ = img_bgr.shape
        crop = img_bgr[int(h * 0.20):int(h * 0.80), int(w * 0.20):int(w * 0.80)]
        hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(crop, cv2.COLOR_BGR2LAB)
        
        s_fg = hsv[:, :, 1]
        b_fg = lab[:, :, 2]
        a_fg = lab[:, :, 1]
        
        mean_s = float(np.mean(s_fg))
        mean_b = float(np.mean(b_fg))
        mean_a = float(np.mean(a_fg))

        # Bakery check: low saturation tan crumb/crust
        if mean_s < 85 and mean_b < 155 and (mean_a < 135 or category_hint == "Bakery"):
            return "bakery", 0.70
            
        # Dairy check: light uniform cream/white/yellowish dairy texture
        if mean_s < 120 and 125 <= mean_b <= 155 and 122 <= mean_a <= 138:
            return "dairy", 0.65

        # Fallback to category hint if provided
        if category_hint:
            hint_lower = category_hint.strip().lower()
            if hint_lower == "fruit":
                return "fruit", 0.50
            elif hint_lower == "vegetable":
                return "vegetable", 0.50

        # Generic safe fallback
        return "food item", 0.40
