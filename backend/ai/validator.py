import io
import os
import cv2
import numpy as np
from PIL import Image
from fastapi import HTTPException, status
from typing import Tuple, List, Set

class ImageValidator:
    """
    Multi-stage Image Validation Pipeline for Freshco AI:
    Stage 1: File-Level Checks (format, size, corruption, resolution >= 224x224)
    Stage 2: Content-Level Checks (brightness, blur, deep food vs non-food verification)
    """

    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
    MIN_RESOLUTION = (224, 224)  # Width, Height

    BLUR_THRESHOLD = 18.0       # Minimum Laplacian variance for sharpness
    MIN_BRIGHTNESS = 25.0       # Minimum grayscale mean (avoid underexposed/black images)
    MAX_BRIGHTNESS = 246.0      # Maximum grayscale mean (avoid completely blown out images)

    # Pretrained MobileNetV2 food class index cache
    _food_model = None
    _screen_keywords = {
        'web site', 'monitor', 'screen', 'television', 'hand-held computer',
        'cellular telephone', 'menu', 'envelope', 'packet', 'book jacket',
        'comic book', 'scorecard', 'crossword puzzle', 'binder', 'laptop',
        'desktop computer', 'keyboard', 'mouse', 'printer', 'oscilloscope',
        'analog clock', 'digital clock', 'switch', 'dial'
    }

    @classmethod
    def validate_file_level(cls, filename: str, image_bytes: bytes) -> Tuple[int, int]:
        """
        Stage 1: File-level checks before OpenCV decoding.
        Fails fast if corrupted, invalid format, too large, or below 224x224.
        """
        if not image_bytes or len(image_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty or unreadable. Please select a valid image."
            )

        ext = os.path.splitext(filename.lower())[1]
        if ext not in cls.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file format. Only JPG, JPEG, PNG, and WebP images are allowed."
            )

        if len(image_bytes) > cls.MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File size exceeds the 10MB limit. Please upload a smaller image."
            )

        try:
            with Image.open(io.BytesIO(image_bytes)) as pil_img:
                width, height = pil_img.size
                pil_format = (pil_img.format or "").upper()
                if pil_format not in {'JPEG', 'JPG', 'PNG', 'WEBP'}:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid image encoding. Only JPG, JPEG, PNG, and WebP are allowed."
                    )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or unreadable. Please select a valid image."
            )

        if width < cls.MIN_RESOLUTION[0] or height < cls.MIN_RESOLUTION[1]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Image resolution is too low ({width}x{height} detected, minimum 224x224 required). Please provide a higher resolution image."
            )

        return width, height

    @classmethod
    def validate_content_level(cls, img_bgr: np.ndarray):
        """
        Stage 2: Content-level OpenCV & Deep Vision checks on decoded image.
        1. Brightness check (mean pixel intensity)
        2. Blur detection (Laplacian variance)
        3. Deep Food vs Non-Food classification
        """
        if img_bgr is None or img_bgr.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is corrupted or unreadable. Please select a valid image."
            )

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 1. Brightness Check (mean pixel intensity)
        mean_brightness = float(np.mean(gray))
        if mean_brightness < cls.MIN_BRIGHTNESS or mean_brightness > cls.MAX_BRIGHTNESS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Image is too dark/bright, please retake in better lighting"
            )

        # 2. Blur Detection using Laplacian Variance
        gray_norm = cv2.resize(gray, (500, 500), interpolation=cv2.INTER_AREA)
        laplacian_var = float(cv2.Laplacian(gray_norm, cv2.CV_64F).var())
        if laplacian_var < cls.BLUR_THRESHOLD:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Image is too blurry, please retake the photo"
            )

        # 3. Deep Food / Non-Food Verification
        is_food, confidence = cls._verify_food_content(img_bgr)
        if not is_food:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="This doesn't look like a food image. Please upload a clear photo of food to check its freshness."
            )

    @classmethod
    def _init_food_model(cls):
        """Initializes torchvision MobileNetV2 ImageNet-1K food classifier and category indices."""
        if cls._food_model is not None:
            return

        try:
            import torchvision.models as models
            from torchvision.models import MobileNet_V2_Weights

            weights = MobileNet_V2_Weights.DEFAULT
            model = models.mobilenet_v2(weights=weights)
            model.eval()
            cls._food_model = model
            cls._categories = weights.meta['categories']
        except Exception:
            cls._food_model = None
            cls._categories = []

    @classmethod
    def _verify_food_content(cls, img_bgr: np.ndarray) -> Tuple[bool, float]:
        """
        Comprehensive Food vs Non-Food Verification Engine:
        Rejects:
        1. Screenshots, slides, video call windows, and software UIs (straight line geometry)
        2. Deep Vision explicit screen/office/tech objects (MobileNetV2 ImageNet probabilities)
        3. Documents, receipts, code, and ultra-desaturated metal tools
        4. Human portraits, selfies, faces, and apparel
        5. Non-organic flat surfaces and artificial screen glare
        """
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # A. UI / Screenshot / Software Window Geometric Line Check
        # Detects straight horizontal & vertical window frames, cards, tabs, and slide boxes
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=5)
        if lines is not None:
            lines = lines.reshape(-1, 4)
            total_lines = len(lines)
            axis_aligned = 0
            for x1, y1, x2, y2 in lines:
                dx = abs(x2 - x1)
                dy = abs(y2 - y1)
                # Check for nearly horizontal or nearly vertical edge segments
                if dy <= 2 or dx <= 2 or (dx > 0 and (dy / dx < 0.08 or dy / dx > 12)):
                    axis_aligned += 1
            
            axis_ratio = axis_aligned / total_lines if total_lines > 0 else 0.0
            if total_lines >= 30 and axis_aligned >= 20 and axis_ratio > 0.55:
                return False, 0.05

        # B. Deep Vision ImageNet Explicit Non-Food Category Check
        cls._init_food_model()
        if cls._food_model is not None:
            try:
                import torch
                img_rgb = cv2.cvtColor(cv2.resize(img_bgr, (224, 224), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2RGB)
                mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
                std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
                tensor = (torch.tensor(img_rgb, dtype=torch.float32).permute(2, 0, 1).unsqueeze(0) / 255.0 - mean) / std

                with torch.no_grad():
                    logits = cls._food_model(tensor)
                    probs = torch.softmax(logits, dim=1).numpy()[0]

                top5_idx = np.argsort(probs)[-5:][::-1]
                top1_cat = cls._categories[top5_idx[0]].lower()
                top1_prob = float(probs[top5_idx[0]])

                # If top category is unambiguously a digital screen, website, monitor, or office object
                if any(k in top1_cat for k in cls._screen_keywords) and top1_prob > 0.10:
                    return False, 0.05

            except Exception:
                pass

        # C. Color & Texture Analysis
        img_resized = cv2.resize(img_bgr, (256, 256), interpolation=cv2.INTER_AREA)
        hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
        lab = cv2.cvtColor(img_resized, cv2.COLOR_BGR2LAB)
        
        h_channel, s_channel, v_channel = cv2.split(hsv)
        l_channel, a_channel, b_channel = cv2.split(lab)

        mean_sat = float(np.mean(s_channel))
        sat_p75 = float(np.percentile(s_channel, 75))

        # D. Documents, code, monochrome, or ultra-desaturated metal
        if mean_sat < 15.0 and sat_p75 < 24.0:
            return False, 0.10

        # E. Solid flat background
        if (np.std(l_channel) + np.std(a_channel) + np.std(b_channel)) < 8.0:
            return False, 0.10

        # F. Artificial cyan screen glare (> 50%)
        artificial_cyan_blue = ((h_channel > 88) & (h_channel < 128)) & (s_channel > 75)
        cyan_ratio = float(np.sum(artificial_cyan_blue) / artificial_cyan_blue.size)
        if cyan_ratio > 0.50:
            return False, 0.15

        # G. Human Portrait / Face / Clothing Detection
        skin_mask = ((h_channel <= 20) | (h_channel >= 170)) & (s_channel >= 30) & (s_channel <= 160) & (v_channel > 70) & (a_channel >= 134) & (a_channel <= 162) & (b_channel >= 134) & (b_channel <= 165)
        skin_ratio = float(np.sum(skin_mask) / skin_mask.size)

        textile_mask = (h_channel >= 90) & (h_channel <= 135) & (s_channel > 50)
        textile_ratio = float(np.sum(textile_mask) / textile_mask.size)

        if skin_ratio > 0.10 and textile_ratio > 0.05:
            return False, 0.15

        # H. Organic Food Chromatic Footprint
        organic_food_pixels = ((h_channel <= 85) | (h_channel >= 130)) & (s_channel > 28) & (v_channel > 25)
        organic_count = int(np.sum(organic_food_pixels))

        if organic_count < 1200:
            return False, 0.15

        return True, 0.90
