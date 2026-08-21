import io
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from typing import Dict, Any, Tuple
from config import settings

class ImagePreprocessor:
    """
    Image Preprocessing & Defect Extraction Pipeline for Freshco AI:
    - EXIF auto-rotation to correct smartphone camera orientation
    - Contrast Limited Adaptive Histogram Equalization (CLAHE) on LAB L-channel for MobileNetV2 CNN
    - Bilateral edge-preserving denoising
    - Morphological Black Top-Hat & Relative-Contrast defect extraction on clean denoised channels:
        * Ignores smooth ambient lighting gradients, side curvature, and natural shadows
        * Distinguishes smooth biological ripening blushes (mango, peach, apple) from necrotic lesions
        * Excludes healthy chlorophyll green leaves/stems while detecting genuine fungal mold
    - Anti-aliased 224x224 interpolation (cv2.INTER_AREA) with [-1.0, 1.0] scaling
    """

    TARGET_SIZE = (224, 224)

    @classmethod
    def load_image_from_bytes(cls, image_bytes: bytes) -> np.ndarray:
        """
        Loads image bytes with EXIF rotation auto-correction via PIL,
        converting directly into a standard BGR NumPy array for OpenCV.
        """
        pil_image = Image.open(io.BytesIO(image_bytes))
        pil_image = ImageOps.exif_transpose(pil_image)
        rgb_image = pil_image.convert('RGB')
        rgb_array = np.array(rgb_image)
        bgr_array = cv2.cvtColor(rgb_array, cv2.COLOR_RGB2BGR)
        return bgr_array

    @classmethod
    def normalize_lighting_and_denoise(cls, img_bgr: np.ndarray) -> np.ndarray:
        """
        Applies CLAHE on the L (Lightness) channel in LAB color space
        and bilateral filtering to remove sensor grain while preserving defect edges.
        """
        lab = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2LAB)
        l_channel, a_channel, b_channel = cv2.split(lab)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l_equalized = clahe.apply(l_channel)

        lab_equalized = cv2.merge((l_equalized, a_channel, b_channel))
        img_equalized_bgr = cv2.cvtColor(lab_equalized, cv2.COLOR_LAB2BGR)

        img_denoised = cv2.bilateralFilter(img_equalized_bgr, d=5, sigmaColor=35, sigmaSpace=35)
        return img_denoised

    @classmethod
    def preprocess_for_model(cls, img_bgr: np.ndarray) -> np.ndarray:
        """
        Full MobileNetV2 preprocessing pipeline:
        1. Lighting normalization (CLAHE)
        2. High-quality interpolation resizing to 224x224 (cv2.INTER_AREA for downscale)
        3. Convert BGR to RGB
        4. MobileNetV2 normalization to exact [-1.0, 1.0] range
        """
        img_enhanced = cls.normalize_lighting_and_denoise(img_bgr)

        h, w = img_enhanced.shape[:2]
        if w > cls.TARGET_SIZE[0] or h > cls.TARGET_SIZE[1]:
            img_resized = cv2.resize(img_enhanced, cls.TARGET_SIZE, interpolation=cv2.INTER_AREA)
        else:
            img_resized = cv2.resize(img_enhanced, cls.TARGET_SIZE, interpolation=cv2.INTER_CUBIC)

        img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
        normalized = (img_rgb.astype(np.float32) / 127.5) - 1.0
        return np.expand_dims(normalized, axis=0)

    @classmethod
    def extract_visual_defect_metrics(cls, img_bgr: np.ndarray, category_hint: str = "General") -> Dict[str, float]:
        """
        Calibrated Visual Inspection Metrics using Black Top-Hat & Relative-Contrast:
        - Uses clean bilateral-denoised channels without artificial CLAHE edge exaggeration
        - Morphological Black Top-Hat on L-channel isolates localized dark spots and sugar spots
        - Relative-contrast oxidation detection on pale flesh (cut apple, banana, pear)
        - Red meat myoglobin air oxidation strictly scoped to meat category
        - Fungal mold spore detection (excludes healthy chlorophyll green leaves/stems)
        - Localized spatial gradient Discoloration Index (smooth multi-tone blush != rot)
        - Texture Homogeneity via Laplacian variance
        """
        img_denoised = cv2.bilateralFilter(img_bgr, d=5, sigmaColor=35, sigmaSpace=35)
        img_resized = cv2.resize(img_denoised, (256, 256), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

        l_channel, a_channel, b_channel = cv2.split(lab)
        h_channel, s_channel, v_channel = cv2.split(hsv)

        # 1. Foreground Food Mask: Segment saturated/colored food body and close internal defect holes
        food_pixels = (s_channel > 25) | (np.abs(a_channel.astype(int) - 128) > 8) | (np.abs(b_channel.astype(int) - 128) > 8)
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (35, 35))
        fg_mask = cv2.morphologyEx(food_pixels.astype(np.uint8), cv2.MORPH_CLOSE, kernel_close).astype(bool)
        fg_pixels = int(np.sum(fg_mask))
        if fg_pixels < 400:
            fg_mask = np.ones((256, 256), dtype=bool)
            fg_pixels = 256 * 256

        med_l = float(np.median(l_channel[fg_mask]))
        med_a = float(np.median(a_channel[fg_mask]))

        # 2. Localized Dark Necrotic Spots & Sugar Spots via Black Top-Hat
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
        tophat = cv2.morphologyEx(l_channel, cv2.MORPH_BLACKHAT, kernel)
        local_spots = (tophat > 22) & (v_channel < 95) & fg_mask

        # 3. Deep Necrotic Rot & Melanin Collapse (absolute low lightness)
        deep_rot = (l_channel < 45) & (v_channel < 60) & fg_mask

        # 4. Pale Flesh Enzymatic Browning (cut apple, banana, pear, potato)
        pale_browning = (med_l > 175) & (l_channel < med_l - 25.0) & (h_channel >= 8) & (h_channel <= 28) & fg_mask

        # 5. Red Meat Myoglobin Air Oxidation (Strictly scoped to Meat category)
        meat_oxidation = np.zeros_like(fg_mask)
        if category_hint == "Meat":
            meat_oxidation = (a_channel < 138) & (h_channel >= 8) & (h_channel <= 30) & (v_channel < 150) & fg_mask

        # 6. Fungal Mold Spores (powdery green/grey/white mycelium patches on produce, excluding healthy chlorophyll leaves)
        healthy_leaf = (h_channel >= 34) & (h_channel <= 88) & (a_channel <= 112) & (s_channel >= 40) & (v_channel >= 60)
        mold_candidate = ((h_channel >= 30) & (h_channel <= 95) & (s_channel < 80) & (l_channel > 40) & (l_channel < 225) & (v_channel < 185)) & fg_mask
        mold_mask = mold_candidate & (~healthy_leaf)

        # 7. Bacterial Green Slime (Strictly for Meat/Proteins)
        bacterial_slime = np.zeros_like(fg_mask)
        if category_hint == "Meat":
            bacterial_slime = (a_channel < 122) & (h_channel >= 35) & (h_channel <= 95) & (v_channel < 140) & fg_mask

        browning_mask = pale_browning | local_spots | meat_oxidation

        combined_defect_mask = local_spots | deep_rot | pale_browning | meat_oxidation | mold_mask | bacterial_slime
        defect_pixel_count = int(np.sum(combined_defect_mask))
        spot_coverage_pct = round(float((defect_pixel_count / fg_pixels) * 100.0), 2)

        # 8. Localized Spatial Gradient Discoloration Index:
        # Measures high-frequency local color roughness (rot lesions) while ignoring smooth biological ripening blushes
        lap_a = cv2.Laplacian(a_channel, cv2.CV_64F)
        lap_b = cv2.Laplacian(b_channel, cv2.CV_64F)
        a_lap_fg = lap_a[fg_mask]
        b_lap_fg = lap_b[fg_mask]
        if len(a_lap_fg) > 0:
            discoloration_index = round(float((np.std(a_lap_fg) + np.std(b_lap_fg)) / 2.0), 2)
        else:
            discoloration_index = 3.5

        # 9. Surface Texture Homogeneity / Roughness
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian_fg = laplacian[fg_mask]
        laplacian_var = float(np.var(laplacian_fg)) if len(laplacian_fg) > 0 else 50.0
        surface_homogeneity = round(float(max(0.0, min(100.0, 100.0 - (laplacian_var / 30.0)))), 2)

        # 10. Browning Score (0.0 to 10.0 scale)
        browning_pixels = np.sum(browning_mask | deep_rot | mold_mask)
        browning_score = round(float(min(10.0, ((browning_pixels / fg_pixels) * 15.0) + (spot_coverage_pct * 0.10))), 2)

        return {
            "discoloration_index": discoloration_index,
            "spot_coverage_pct": spot_coverage_pct,
            "surface_homogeneity": surface_homogeneity,
            "browning_score": browning_score
        }
