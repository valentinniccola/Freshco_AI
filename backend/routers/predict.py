import os
import json
import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import PredictionRecord, User
from schemas import PredictionResponse, Probabilities, DefectMetrics, RecipeSuggestion
from auth import get_current_user
from ai.validator import ImageValidator
from ai.preprocessor import ImagePreprocessor
from ai.model import classifier
from ai.shelf_life import ShelfLifeEstimator
from ai.food_classifier import FoodTypeClassifier
from ai.recipe_service import RecipeService
from rate_limiter import upload_rate_limiter
from config import settings

router = APIRouter(prefix="/api/predict", tags=["Prediction"])

SAMPLE_METADATA = [
    {
        "id": "sample_apple_fresh",
        "name": "Crisp Fuji Apple",
        "category": "Fruit",
        "expected": "Fresh",
        "filename": "apple_fresh.jpg",
        "url": "/static/samples/apple_fresh.jpg"
    },
    {
        "id": "sample_banana_nearly_spoiled",
        "name": "Spotted Banana",
        "category": "Fruit",
        "expected": "Nearly Spoiled",
        "filename": "banana_spotted.jpg",
        "url": "/static/samples/banana_spotted.jpg"
    },
    {
        "id": "sample_tomato_fresh",
        "name": "Ripe Vine Tomato",
        "category": "Vegetable",
        "expected": "Fresh",
        "filename": "tomato_fresh.jpg",
        "url": "/static/samples/tomato_fresh.jpg"
    },
    {
        "id": "sample_orange_spoiled",
        "name": "Deteriorated Orange",
        "category": "Fruit",
        "expected": "Spoiled",
        "filename": "orange_spoiled.jpg",
        "url": "/static/samples/orange_spoiled.jpg"
    },
    {
        "id": "sample_bread_spoiled",
        "name": "Moldy Bakery Bread",
        "category": "Bakery",
        "expected": "Spoiled",
        "filename": "bread_spoiled.jpg",
        "url": "/static/samples/bread_spoiled.jpg"
    },
    {
        "id": "sample_meat_fresh",
        "name": "Fresh Beef Steak",
        "category": "Meat",
        "expected": "Fresh",
        "filename": "meat_fresh.jpg",
        "url": "/static/samples/meat_fresh.jpg"
    }
]

@router.get("/samples")
def get_sample_images():
    """
    Returns pre-bundled sample food images with metadata for quick testing.
    """
    return SAMPLE_METADATA

@router.post("", response_model=PredictionResponse)
async def predict_food_freshness(
    file: Optional[UploadFile] = File(None),
    sample_id: Optional[str] = Form(None),
    category: str = Form("General"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Analyzes food image freshness with multi-stage validation:
    1. System-Level: Rate Limiting & User Auth
    2. File-Level Validation: Format, Size, Corruption, Resolution >= 224x224
    3. Content-Level Validation: Blur detection, Brightness check, Food/Non-food detection
    4. Food Type Identification: Detects specific food item (banana, apple, tomato, etc.)
    5. MobileNetV2 Freshness Classification & Output Validation
    6. Recipe Suggestions: Triggered exclusively for 'Nearly Spoiled' items
    """
    # 1. Rate Limiting Check
    upload_rate_limiter.check_rate_limit(str(current_user.id))

    original_filename = "food_image.jpg"
    image_bytes = None
    relative_image_url = ""

    if file and file.filename:
        original_filename = file.filename
        image_bytes = await file.read()
        
        # 2. Stage 1: File-Level Validation
        ImageValidator.validate_file_level(original_filename, image_bytes)

        ext = os.path.splitext(file.filename)[1] or ".jpg"
        unique_name = f"{uuid.uuid4().hex}{ext}"
        save_path = settings.UPLOAD_DIR / unique_name
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        relative_image_url = f"/uploads/{unique_name}"

    elif sample_id:
        sample_item = next((s for s in SAMPLE_METADATA if s["id"] == sample_id), None)
        if not sample_item:
            raise HTTPException(status_code=400, detail=f"Sample '{sample_id}' not found.")
        
        sample_path = settings.STATIC_DIR / "samples" / sample_item["filename"]
        if not sample_path.exists():
            raise HTTPException(status_code=404, detail="Sample image file missing.")
            
        with open(sample_path, "rb") as f:
            image_bytes = f.read()
            
        original_filename = sample_item["name"]
        category = sample_item["category"]
        relative_image_url = sample_item["url"]
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either an image file upload or a valid sample_id must be provided."
        )

    # 3. OpenCV Decoding with EXIF orientation correction & Stage 2 Content Checks
    img_bgr = ImagePreprocessor.load_image_from_bytes(image_bytes)
    ImageValidator.validate_content_level(img_bgr)

    # 4. Food Type Identification Step
    food_type, food_type_conf = FoodTypeClassifier.identify_food_type(img_bgr, category_hint=category)

    # 5. AI Inference & Stage 3: Model-Output Level Checks
    pred_data = classifier.predict(img_bgr, category_hint=category, food_type_hint=food_type)
    
    freshness = pred_data["freshness"]
    confidence = pred_data["confidence"]
    all_probabilities = pred_data["all_probabilities"]
    freshness_status = pred_data["freshness_status"]
    confidence_score = pred_data["confidence_score"]
    probabilities = pred_data["probabilities"]
    defect_metrics = pred_data["defect_metrics"]
    is_uncertain = pred_data["is_uncertain"]
    is_low_confidence = pred_data["is_low_confidence"]
    candidate_classes = pred_data["candidate_classes"]
    status_message = pred_data["status_message"]
    primary_class = pred_data["primary_predicted_class"]

    # 6. Recipe Suggestions for 'Nearly Spoiled' Items
    recipe_suggestions = None
    if primary_class == "Nearly Spoiled" or freshness_status == "Nearly Spoiled" or ("Nearly Spoiled" in candidate_classes):
        raw_recipes = RecipeService.get_recipes_for_food(food_type)
        recipe_suggestions = [RecipeSuggestion(**r) for r in raw_recipes]

    # 7. Shelf-Life Estimation & Storage Guidance
    shelf_life_info = ShelfLifeEstimator.estimate(
        freshness_status=primary_class,
        food_category=category,
        defect_metrics=defect_metrics
    )

    # 8. Save Record to SQLite DB
    record = PredictionRecord(
        user_id=current_user.id,
        image_path=relative_image_url,
        original_filename=original_filename,
        food_category=category,
        freshness_status=freshness_status,
        confidence_score=confidence_score,
        probabilities_json=json.dumps(probabilities),
        shelf_life_days=shelf_life_info["shelf_life_days"],
        shelf_life_desc=shelf_life_info["shelf_life_desc"],
        storage_advice=shelf_life_info["storage_advice"],
        defect_metrics_json=json.dumps(defect_metrics),
        created_at=datetime.utcnow()
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResponse(
        id=record.id,
        image_url=relative_image_url,
        original_filename=original_filename,
        food_category=category,
        food_type=food_type,
        freshness=freshness,
        confidence=confidence,
        all_probabilities=all_probabilities,
        freshness_status=freshness_status,
        confidence_score=confidence_score,
        probabilities=Probabilities(**probabilities),
        shelf_life_days=shelf_life_info["shelf_life_days"],
        shelf_life_desc=shelf_life_info["shelf_life_desc"],
        storage_advice=shelf_life_info["storage_advice"],
        defect_metrics=DefectMetrics(**defect_metrics),
        action_recommendation=shelf_life_info["action_recommendation"],
        recipe_suggestions=recipe_suggestions,
        is_uncertain=is_uncertain,
        is_low_confidence=is_low_confidence,
        candidate_classes=candidate_classes,
        status_message=status_message,
        created_at=record.created_at
    )
