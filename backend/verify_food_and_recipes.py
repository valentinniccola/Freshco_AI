import cv2
import numpy as np
from ai.food_classifier import FoodTypeClassifier
from ai.model import classifier
from ai.recipe_service import RecipeService

samples = ['apple_fresh.jpg', 'banana_spotted.jpg', 'tomato_fresh.jpg', 'orange_spoiled.jpg', 'bread_spoiled.jpg', 'meat_fresh.jpg']

for name in samples:
    with open(f'static/samples/{name}', 'rb') as f:
        bytes_data = f.read()
    img = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    food, f_conf = FoodTypeClassifier.identify_food_type(img)
    pred = classifier.predict(img)
    status = pred["freshness_status"]
    
    recipes = []
    if status == "Nearly Spoiled" or pred["primary_predicted_class"] == "Nearly Spoiled":
        recipes = RecipeService.get_recipes_for_food(food)
        
    print(f"=== {name} ===")
    print(f"Detected Food Type: {food} (Confidence: {f_conf*100:.0f}%)")
    print(f"Freshness Status:   {status} (Confidence: {pred['confidence_score']*100:.1f}%)")
    print(f"Recipe Suggestions: {len(recipes)} recipes found")
    for r in recipes:
        print(f"  - {r['title']} ({r['prep_time']})")
    print("-" * 50)
