import os
import requests
from typing import List, Dict, Any

class RecipeService:
    """
    Recipe Suggestion Service for Nearly Spoiled Food Items:
    - Queries Spoonacular API if SPOONACULAR_API_KEY is present
    - Uses an embedded zero-waste offline recipe catalog for 100% reliable offline/demo operation.
    """

    OFFLINE_RECIPES: Dict[str, List[Dict[str, str]]] = {
        "banana": [
            {
                "title": "Classic Overripe Banana Bread",
                "description": "Transform spotted bananas into a moist, aromatic loaf with cinnamon and walnuts.",
                "prep_time": "10 mins prep, 50 mins bake",
                "source_url": "https://www.allrecipes.com/recipe/20144/banana-banana-bread/",
                "difficulty": "Easy"
            },
            {
                "title": "Quick 3-Ingredient Banana Pancakes",
                "description": "Mash overripe bananas with eggs and a pinch of cinnamon for light, flourless pancakes.",
                "prep_time": "15 mins",
                "source_url": "https://www.allrecipes.com/recipe/244440/three-ingredient-banana-pancakes/",
                "difficulty": "Beginner"
            },
            {
                "title": "Creamy Frozen Banana Smoothie / Nice Cream",
                "description": "Peel, slice, freeze, and blend with milk or cocoa for dairy-free healthy soft-serve.",
                "prep_time": "5 mins",
                "source_url": "https://www.allrecipes.com/recipe/238712/banana-nice-cream/",
                "difficulty": "Super Quick"
            }
        ],
        "apple": [
            {
                "title": "Spiced Cinnamon Apple Compote",
                "description": "Simmer softened apples with cinnamon, brown sugar, and lemon juice for pancakes or oatmeal topping.",
                "prep_time": "20 mins",
                "source_url": "https://www.allrecipes.com/recipe/234769/cinnamon-apple-compote/",
                "difficulty": "Easy"
            },
            {
                "title": "Rustic 15-Minute Apple Crumble",
                "description": "Bake sliced apples with an oat, butter, and brown sugar streusel crust.",
                "prep_time": "30 mins",
                "source_url": "https://www.allrecipes.com/recipe/219163/easy-apple-crisp/",
                "difficulty": "Easy"
            },
            {
                "title": "Homemade Apple Butter Spread",
                "description": "Slow cook pureed apples with spices until dark, caramelized, and spreadable.",
                "prep_time": "45 mins",
                "source_url": "https://www.allrecipes.com/recipe/18063/slow-cooker-apple-butter/",
                "difficulty": "Medium"
            }
        ],
        "tomato": [
            {
                "title": "Roasted Garlic & Tomato Pasta Sauce",
                "description": "Roast softened tomatoes with olive oil, whole garlic cloves, and basil for rich pasta sauce.",
                "prep_time": "25 mins",
                "source_url": "https://www.allrecipes.com/recipe/11966/fresh-tomato-pasta-sauce/",
                "difficulty": "Easy"
            },
            {
                "title": "Hearty Tuscan Tomato & Basil Soup",
                "description": "Simmer ripe tomatoes with vegetable broth, heavy cream or coconut milk, and sourdough croutons.",
                "prep_time": "20 mins",
                "source_url": "https://www.allrecipes.com/recipe/230109/fresh-tomato-soup/",
                "difficulty": "Easy"
            },
            {
                "title": "Sun-Dried Style Slow Roast Tomatoes",
                "description": "Halve tomatoes and bake low and slow at 120°C with herbs for umami salad toppers.",
                "prep_time": "1 hour",
                "source_url": "https://www.allrecipes.com/recipe/228828/slow-roasted-cherry-tomatoes/",
                "difficulty": "Easy"
            }
        ],
        "orange": [
            {
                "title": "Zero-Waste Citrus Marmalade",
                "description": "Boil sliced oranges with sugar and lemon juice for a tangy homemade breakfast spread.",
                "prep_time": "40 mins",
                "source_url": "https://www.allrecipes.com/recipe/238698/orange-marmalade/",
                "difficulty": "Medium"
            },
            {
                "title": "Candied Orange Peel & Glaze",
                "description": "Simmer orange rinds in simple syrup for dessert garnishes or chocolate dipping.",
                "prep_time": "30 mins",
                "source_url": "https://www.allrecipes.com/recipe/24227/candied-orange-peel/",
                "difficulty": "Easy"
            }
        ],
        "bread": [
            {
                "title": "Crispy Garlic & Herb Croutons",
                "description": "Cube stale bread, toss in olive oil, garlic powder, and oregano, and bake until golden brown.",
                "prep_time": "15 mins",
                "source_url": "https://www.allrecipes.com/recipe/14589/homemade-croutons/",
                "difficulty": "Super Quick"
            },
            {
                "title": "Golden Vanilla French Toast",
                "description": "Stale bread absorbs egg custard perfectly without falling apart. Pan fry with butter.",
                "prep_time": "15 mins",
                "source_url": "https://www.allrecipes.com/recipe/7016/french-toast-i/",
                "difficulty": "Easy"
            },
            {
                "title": "Italian Pangrattato (Crunchy Breadcrumb Topping)",
                "description": "Pulse stale bread in a food processor and toast in garlic oil for pasta and soup crisping.",
                "prep_time": "10 mins",
                "source_url": "https://www.allrecipes.com/recipe/222359/how-to-make-fresh-breadcrumbs/",
                "difficulty": "Easy"
            }
        ],
        "meat": [
            {
                "title": "High-Heat Stir-Fry with Crisp Veggies",
                "description": "Slice meat thin and cook at high heat with soy sauce, garlic, and ginger to ensure thorough cooking.",
                "prep_time": "20 mins",
                "source_url": "https://www.allrecipes.com/recipe/228823/quick-beef-stir-fry/",
                "difficulty": "Easy"
            },
            {
                "title": "Slow-Simmered Chili / Stew",
                "description": "Brown meat and simmer with beans, crushed tomatoes, and spices for deep flavor.",
                "prep_time": "45 mins",
                "source_url": "https://www.allrecipes.com/recipe/78299/boils-more-beef-stew/",
                "difficulty": "Medium"
            }
        ],
        "spinach": [
            {
                "title": "Spinach & Feta Breakfast Frittata",
                "description": "Sauté wilting spinach and bake with whisked eggs, cheese, and herbs.",
                "prep_time": "20 mins",
                "source_url": "https://www.allrecipes.com/recipe/15003/spinach-and-cheese-frittata/",
                "difficulty": "Easy"
            },
            {
                "title": "Creamy Garlic Sautéed Spinach",
                "description": "Flash wilt spinach with butter, minced garlic, and parmesan cheese in 5 minutes.",
                "prep_time": "8 mins",
                "source_url": "https://www.allrecipes.com/recipe/238477/sauteed-spinach-with-garlic/",
                "difficulty": "Super Quick"
            }
        ],
        "food item": [
            {
                "title": "Zero-Waste Savory Food Broth",
                "description": "Simmer softened produce and aromatic trims with water and herbs to extract rich cooking stock.",
                "prep_time": "35 mins",
                "source_url": "https://www.allrecipes.com/recipe/12982/basic-vegetable-stock/",
                "difficulty": "Easy"
            },
            {
                "title": "All-Ingredient Kitchen-Sink Stir Fry",
                "description": "Chop and flash sauté with garlic, soy sauce, and sesame oil over rice or noodles.",
                "prep_time": "15 mins",
                "source_url": "https://www.allrecipes.com/recipe/223382/stir-fry-sauce/",
                "difficulty": "Easy"
            },
            {
                "title": "Blanch & Freeze Meal Prep",
                "description": "Blanch in boiling water for 90 seconds, plunge into ice water, and freeze in airtight portions.",
                "prep_time": "10 mins",
                "source_url": "https://www.allrecipes.com/article/how-to-freeze-vegetables/",
                "difficulty": "Preservation"
            }
        ]
    }

    @classmethod
    def get_recipes_for_food(cls, food_type: str) -> List[Dict[str, str]]:
        """
        Retrieves 2-3 recipe recommendations for the specified food ingredient.
        """
        api_key = os.getenv("SPOONACULAR_API_KEY")
        if api_key:
            try:
                url = f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={food_type}&number=3&ranking=2&apiKey={api_key}"
                res = requests.get(url, timeout=3.0)
                if res.status_code == 200:
                    data = res.json()
                    if isinstance(data, list) and len(data) > 0:
                        recipes = []
                        for item in data[:3]:
                            recipes.append({
                                "title": item.get("title", f"Quick {food_type.title()} Recipe"),
                                "description": f"Uses {food_type} as a primary ingredient to prevent food waste.",
                                "prep_time": "20-30 mins",
                                "source_url": f"https://spoonacular.com/recipes/{item.get('title', '').replace(' ', '-').lower()}-{item.get('id')}",
                                "difficulty": "Easy"
                            })
                        return recipes
            except Exception as e:
                print(f"[RecipeService] Spoonacular API lookup fallback: {e}")

        # Use offline catalog
        normalized_food = food_type.lower().strip()
        if normalized_food in cls.OFFLINE_RECIPES:
            return cls.OFFLINE_RECIPES[normalized_food]

        # Check partial match
        for key in cls.OFFLINE_RECIPES:
            if key in normalized_food:
                return cls.OFFLINE_RECIPES[key]

        return cls.OFFLINE_RECIPES["food item"]
