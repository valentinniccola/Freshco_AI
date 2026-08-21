from typing import Dict, Any, Tuple

class ShelfLifeEstimator:
    """
    Expert rule engine for estimating approximate food shelf-life,
    storage recommendations, and safety handling instructions.
    """

    FOOD_DATA = {
        "Fruit": {
            "Fresh": {
                "shelf_life_days": 7,
                "shelf_life_desc": "5 to 8 days under refrigeration",
                "storage_advice": "Store in a breathable produce drawer at 2°C - 4°C. Keep high ethylene producers (apples, bananas) separate from sensitive fruits.",
                "action_recommendation": "Optimal condition. Safe for raw consumption."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 2,
                "shelf_life_desc": "1 to 2 days maximum",
                "storage_advice": "Consume immediately, blend into smoothies, cook into jam/compote, or slice and freeze at -18°C.",
                "action_recommendation": "Approaching spoilage. Trim minor blemishes and consume or freeze within 24–48 hours."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Expired / Deteriorated)",
                "storage_advice": "Discard in organic waste/compost. Sanitize the storage container to prevent cross-contamination.",
                "action_recommendation": "Unsafe for consumption. Microbial or fungal spoilage detected. Do not ingest."
            }
        },
        "Vegetable": {
            "Fresh": {
                "shelf_life_days": 6,
                "shelf_life_desc": "4 to 7 days in high humidity crisper drawer",
                "storage_advice": "Keep in perforated bags or crisper drawer at 3°C - 5°C. Avoid washing until right before consumption.",
                "action_recommendation": "Fresh and crisp. Excellent for raw salads or cooking."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 2,
                "shelf_life_desc": "1 to 2 days before total spoilage",
                "storage_advice": "Chop and cook into soups, broths, stir-fries, or blanch and freeze immediately.",
                "action_recommendation": "Wilting or minor softening detected. Cook thoroughly before consumption."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Spoiled)",
                "storage_advice": "Compost or safely discard. Clean refrigerator surface thoroughly.",
                "action_recommendation": "Rotting, slimy texture, or mold detected. Discard immediately."
            }
        },
        "Meat": {
            "Fresh": {
                "shelf_life_days": 3,
                "shelf_life_desc": "2 to 3 days in coldest refrigerator shelf (0°C - 2°C)",
                "storage_advice": "Keep tightly sealed in original packaging or airtight vacuum pack on the bottom shelf. Freeze for long-term storage (3-6 months).",
                "action_recommendation": "Prime freshness. Cook thoroughly to recommended internal temperature."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 1,
                "shelf_life_desc": "Less than 24 hours",
                "storage_advice": "Cook thoroughly right away or freeze immediately. Check for sour odors or tackiness.",
                "action_recommendation": "Surface color shifting detected. Cook immediately at high heat if no foul odor is present."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Spoiled / High Danger)",
                "storage_advice": "Double bag and discard in trash immediately. Do not feed to pets.",
                "action_recommendation": "Severe spoilage / bacterial hazard. Do not consume under any circumstances."
            }
        },
        "Dairy": {
            "Fresh": {
                "shelf_life_days": 7,
                "shelf_life_desc": "5 to 9 days under constant refrigeration",
                "storage_advice": "Maintain at 1°C - 4°C inside the fridge (avoid the door shelves where temperature fluctuates). Keep sealed.",
                "action_recommendation": "Fresh and safe for drinking or cooking."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 1,
                "shelf_life_desc": "1 day maximum",
                "storage_advice": "Use immediately for baking or heated dishes if taste/smell remains acceptable.",
                "action_recommendation": "Approaching turning point. Inspect for separation or odor before use."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Curdled / Spoiled)",
                "storage_advice": "Discard safely down the drain or trash bin. Clean container.",
                "action_recommendation": "Sour curdling or mold detected. Discard immediately."
            }
        },
        "Bakery": {
            "Fresh": {
                "shelf_life_days": 4,
                "shelf_life_desc": "3 to 5 days in a cool, dry bread box",
                "storage_advice": "Keep at room temperature in a sealed bag or breadbox. Avoid refrigerating bread as it accelerates staling; freeze instead for long preservation.",
                "action_recommendation": "Soft and fresh. Ready to eat."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 1,
                "shelf_life_desc": "1 day (Stale/Drying)",
                "storage_advice": "Toast, turn into breadcrumbs/croutons, or make French toast.",
                "action_recommendation": "Staling detected. Safe to toast or bake if no mold spores are visible."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Mold Growth)",
                "storage_advice": "Discard the entire loaf. Mold roots penetrate deeply even where invisible.",
                "action_recommendation": "Visible mold colonies detected. Do not cut off mold—discard the whole item."
            }
        },
        "General": {
            "Fresh": {
                "shelf_life_days": 5,
                "shelf_life_desc": "3 to 6 days under proper refrigerated conditions",
                "storage_advice": "Store in an airtight container at 2°C - 4°C away from direct sunlight.",
                "action_recommendation": "High freshness score. Safe for immediate consumption."
            },
            "Nearly Spoiled": {
                "shelf_life_days": 1,
                "shelf_life_desc": "1 to 2 days remaining",
                "storage_advice": "Plan to consume today or freeze in airtight portions.",
                "action_recommendation": "Early visual signs of breakdown. Prioritize consumption."
            },
            "Spoiled": {
                "shelf_life_days": 0,
                "shelf_life_desc": "0 days (Expired / Spoiled)",
                "storage_advice": "Discard safely in food waste disposal.",
                "action_recommendation": "Signs of visual spoilage detected. Do not consume."
            }
        }
    }

    @classmethod
    def estimate(cls, freshness_status: str, food_category: str = "General", defect_metrics: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Calculates shelf life days, detailed advice, and handles category fallback.
        """
        category_key = food_category if food_category in cls.FOOD_DATA else "General"
        status_key = freshness_status if freshness_status in ["Fresh", "Nearly Spoiled", "Spoiled"] else "Fresh"
        
        info = cls.FOOD_DATA[category_key][status_key]
        
        # Fine-tune days if defect metrics show border-line degradation
        adjusted_days = info["shelf_life_days"]
        if status_key == "Fresh" and defect_metrics:
            if defect_metrics.get("spot_coverage_pct", 0) > 12.0 or defect_metrics.get("browning_score", 0) > 3.0:
                adjusted_days = max(2, adjusted_days - 2)
        elif status_key == "Nearly Spoiled" and defect_metrics:
            if defect_metrics.get("browning_score", 0) > 6.5:
                adjusted_days = 1

        return {
            "shelf_life_days": adjusted_days,
            "shelf_life_desc": info["shelf_life_desc"],
            "storage_advice": info["storage_advice"],
            "action_recommendation": info["action_recommendation"]
        }
