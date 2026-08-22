import os
import json
import random
from typing import List, Dict, Any, Optional
from config import settings

class AgentRecipeService:
    """
    Agentic Multi-Item Recipe Engine:
    Synthesizes single zero-waste culinary recipes combining multiple nearly spoiled ingredients.
    Uses Anthropic Claude LLM when ANTHROPIC_API_KEY is available, with an intelligent culinary fallback.
    """

    @classmethod
    def generate_combined_recipe(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a list of scanned items: [{'food_type': 'banana', 'scan_id': 1, 'shelf_life_days': 2}, ...]
        Returns a structured multi-item recipe.
        """
        food_names = [item.get("food_type", "food item").lower() for item in items]
        unique_foods = list(dict.fromkeys(food_names))

        # 1. Attempt Anthropic Claude LLM Call if API key configured
        if settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip():
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY.strip())

                prompt_items_desc = "\n".join([
                    f"- Item #{idx+1}: {it.get('food_type', 'Produce').capitalize()} (Status: Nearly Spoiled, ~{it.get('shelf_life_days', 1)} days remaining, Scan ID #{it.get('scan_id')})"
                    for idx, it in enumerate(items)
                ])

                system_prompt = (
                    "You are a Michelin-star zero-waste executive chef and culinary food conservation specialist. "
                    "Your mission is to help home cooks prevent domestic food waste by designing practical, delicious recipes "
                    "that combine MULTIPLE expiring produce items into a single cohesive dish. "
                    "You MUST prioritize items closest to expiring. Common pantry staples (oil, salt, pepper, flour, oats, basic spices) are assumed available. "
                    "You must output STRICT valid JSON with NO commentary or markdown outside the JSON."
                )

                user_prompt = f"""The user has scanned the following produce in their kitchen that are NEARLY SPOILED and must be used immediately:
{prompt_items_desc}

Create a single cohesive, realistic, and delicious recipe that uses AS MANY of these expiring ingredients together as possible.

Return ONLY a JSON object strictly matching this schema:
{{
  "recipe_title": "Recipe Name",
  "tagline": "Brief catchy description highlighting the rescued items",
  "prep_time": "15 mins",
  "cook_time": "20 mins",
  "difficulty": "Easy" | "Medium",
  "used_ingredients": [
    {{
      "food_type": "Food Name",
      "scan_id": {items[0].get('scan_id', 1)},
      "freshness": "Nearly Spoiled",
      "reason": "Why and how this item is utilized in the dish"
    }}
  ],
  "pantry_staples_needed": ["list", "of", "common", "staples"],
  "instructions": [
    "1. Step one...",
    "2. Step two...",
    "3. Step three..."
  ],
  "chef_zero_waste_tip": "Practical tip for food conservation or scrap usage",
  "items_rescued_count": {len(items)},
  "is_agentic": true
}}"""

                response = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )

                response_text = response.content[0].text.strip()
                # Strip markdown fences if present
                if response_text.startswith("```"):
                    lines = response_text.splitlines()
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    response_text = "\n".join(lines).strip()

                parsed_json = json.loads(response_text)
                return parsed_json

            except Exception as e:
                print(f"[Agent Recipe] Claude API call fallback triggered: {e}")

        # 2. Local Zero-Crash Combinatorial Culinary Synthesis Engine
        return cls._local_combinatorial_synthesis(items, unique_foods)

    @classmethod
    def _local_combinatorial_synthesis(cls, items: List[Dict[str, Any]], unique_foods: List[str]) -> Dict[str, Any]:
        """
        Intelligent local multi-ingredient recipe generator.
        Combines sweet, savory, or hybrid produce sets into tested zero-waste culinary recipes.
        """
        has_fruit = any(f in ["banana", "apple", "mango", "orange", "strawberry", "peach"] for f in unique_foods)
        has_veg = any(f in ["tomato", "bellpepper", "carrot", "cucumber", "potato", "spinach"] for f in unique_foods)
        has_meat = any(f in ["meat", "beef", "chicken", "pork", "steak"] for f in unique_foods)
        has_bakery = any(f in ["bread", "bakery", "bun"] for f in unique_foods)

        used_ingredients_list = []
        for it in items:
            ft = it.get("food_type", "Produce").capitalize()
            used_ingredients_list.append({
                "food_type": ft,
                "scan_id": it.get("scan_id"),
                "freshness": "Nearly Spoiled",
                "reason": f"Caramelizes and infuses natural flavor into the dish before spoilage"
            })

        # Recipe Category A: Sweet Fruit Combinations (Bananas, Apples, Mangoes, Strawberries, Oranges)
        if has_fruit and not has_meat and not (has_veg and len(unique_foods) > 2):
            food_title_str = " & ".join([f.capitalize() for f in unique_foods[:2]])
            return {
                "recipe_title": f"Zero-Waste {food_title_str} Spiced Skillet Crumble",
                "tagline": f"Rescues overripe {', '.join(unique_foods)} in a warm, caramelized baked breakfast or dessert",
                "prep_time": "10 mins",
                "cook_time": "20 mins",
                "difficulty": "Easy",
                "used_ingredients": used_ingredients_list,
                "pantry_staples_needed": ["rolled oats", "ground cinnamon", "brown sugar or honey", "butter or coconut oil", "pinch of salt"],
                "instructions": [
                    f"1. Peel and dice the expiring {', '.join(unique_foods)}, cutting away any bruised spots.",
                    "2. Toss the prepared fruit in a pan or baking dish with 1 tsp cinnamon and 1 tbsp honey or brown sugar.",
                    "3. In a small bowl, combine 1 cup rolled oats with 2 tbsp melted butter and a pinch of salt until crumbly.",
                    "4. Top the fruit with the oat crumble and bake at 180°C (350°F) for 20 minutes until bubbling and golden brown.",
                    "5. Serve warm as a nourishing breakfast or dessert."
                ],
                "chef_zero_waste_tip": "Simmer fruit peels and citrus rinds with water and cinnamon sticks to create an aromatic home fragrance or natural herbal tea.",
                "items_rescued_count": len(items),
                "is_agentic": True
            }

        # Recipe Category B: Savory Vegetable / Meat Stir-Fry or Skillet
        elif has_meat or has_veg:
            food_title_str = " & ".join([f.capitalize() for f in unique_foods[:2]])
            return {
                "recipe_title": f"Harvest Zero-Waste {food_title_str} Sauté Skillet",
                "tagline": f"Combines expiring {', '.join(unique_foods)} with garlic and herbs for a hearty skillet meal",
                "prep_time": "12 mins",
                "cook_time": "18 mins",
                "difficulty": "Easy",
                "used_ingredients": used_ingredients_list,
                "pantry_staples_needed": ["olive oil", "garlic", "salt & black pepper", "paprika or Italian seasoning", "lemon juice or vinegar"],
                "instructions": [
                    f"1. Wash and chop the {', '.join(unique_foods)} into uniform bite-sized pieces.",
                    "2. Heat 2 tbsp olive oil in a large skillet over medium-high heat. Add minced garlic.",
                    "3. If using meat, sear thoroughly for 4–5 minutes first, then add root vegetables followed by tender greens/tomatoes.",
                    "4. Season generously with salt, cracked black pepper, and paprika.",
                    "5. Sauté until tender-crisp (6–8 mins). Finish with a squeeze of fresh lemon juice or balsamic vinegar."
                ],
                "chef_zero_waste_tip": "Save vegetable trimmings and stems in a freezer bag to boil into homemade organic vegetable broth.",
                "items_rescued_count": len(items),
                "is_agentic": True
            }

        # Recipe Category C: Bakery Bread Pudding or French Toast Casserole
        elif has_bakery:
            return {
                "recipe_title": "Artisan Bread & Fruit Zero-Waste Pudding",
                "tagline": "Repurposes stale bakery bread and softening fruit into a rich baked casserole",
                "prep_time": "15 mins",
                "cook_time": "30 mins",
                "difficulty": "Easy",
                "used_ingredients": used_ingredients_list,
                "pantry_staples_needed": ["milk (or dairy-free)", "eggs", "vanilla extract", "cinnamon", "sugar"],
                "instructions": [
                    "1. Tear or cube the bread into a greased baking dish.",
                    f"2. Fold in the sliced expiring fruit ({', '.join(unique_foods)}).",
                    "3. Whisk together 2 eggs, 1 cup milk, 1 tsp vanilla, 2 tbsp sugar, and cinnamon.",
                    "4. Pour the custard mixture evenly over the bread and fruit. Let soak for 5 minutes.",
                    "5. Bake at 175°C (350°F) for 25–30 minutes until puffed and set."
                ],
                "chef_zero_waste_tip": "Dry out any leftover crusts completely and pulse in a blender for homemade seasoned breadcrumbs.",
                "items_rescued_count": len(items),
                "is_agentic": True
            }

        # Default Multi-Item Hybrid Bowl
        return {
            "recipe_title": "Zero-Waste Kitchen Medley Power Bowl",
            "tagline": f"Balanced multi-ingredient bowl utilizing {', '.join(unique_foods)}",
            "prep_time": "10 mins",
            "cook_time": "15 mins",
            "difficulty": "Easy",
            "used_ingredients": used_ingredients_list,
            "pantry_staples_needed": ["grains (rice, quinoa, or oats)", "olive oil", "seasonings of choice"],
            "instructions": [
                f"1. Prep all expiring ingredients ({', '.join(unique_foods)}) by slicing and lightly seasoning.",
                "2. Cook or reheat your base grains (rice or quinoa).",
                "3. Quick-sauté or roast the produce until tender and aromatic.",
                "4. Assemble into a colorful bowl and drizzle with your favorite dressing or olive oil."
            ],
            "chef_zero_waste_tip": "Compost non-edible stickers and stems, and freeze any excess cooked grains.",
            "items_rescued_count": len(items),
            "is_agentic": True
        }
