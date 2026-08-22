import json
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from database import get_db
from models import User, PredictionRecord, AgentRecipeLog
from schemas import AgentRecipeResponse
from auth import get_current_user
from ai.agent_recipe import AgentRecipeService
from ai.recipe_service import RecipeService

router = APIRouter(prefix="/api/agent", tags=["Agentic Recipe Engine"])

DAILY_AGENT_CALL_LIMIT = 5

@router.post("/recipe-suggestion", response_model=AgentRecipeResponse)
def get_agentic_recipe_suggestion(
    days: int = Query(default=7, ge=1, le=30, description="Lookback window in days for nearly spoiled scans"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Agentic Multi-Item Recipe Suggestion Engine:
    Finds the user's recent Nearly Spoiled scans (last N days) and synthesizes a single combined zero-waste recipe.
    Rate limited to 5 calls per user per day.
    """
    # 1. Check daily rate limit for LLM calls (5 calls/user/day)
    start_of_day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    calls_today_count = (
        db.query(AgentRecipeLog)
        .filter(
            AgentRecipeLog.user_id == current_user.id,
            AgentRecipeLog.created_at >= start_of_day
        )
        .count()
    )

    if calls_today_count >= DAILY_AGENT_CALL_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Daily AI Recipe limit reached ({DAILY_AGENT_CALL_LIMIT} calls/day). Quota resets at midnight UTC."
        )

    # 2. Query user's nearly spoiled items from last N days
    since_date = datetime.utcnow() - timedelta(days=days)
    recent_nearly_spoiled = (
        db.query(PredictionRecord)
        .filter(
            PredictionRecord.user_id == current_user.id,
            PredictionRecord.freshness_status == "Nearly Spoiled",
            PredictionRecord.created_at >= since_date
        )
        .order_by(PredictionRecord.shelf_life_days.asc(), PredictionRecord.created_at.desc())
        .all()
    )

    # If no nearly spoiled items in history, grab the latest scans or mock demo items
    items_to_use = []
    for record in recent_nearly_spoiled:
        food_type = record.food_category
        try:
            if record.defect_metrics_json:
                metrics = json.loads(record.defect_metrics_json)
                food_type = metrics.get("food_type", record.food_category)
        except Exception:
            pass

        items_to_use.append({
            "food_type": food_type,
            "scan_id": record.id,
            "shelf_life_days": record.shelf_life_days,
            "filename": record.original_filename,
            "created_at": record.created_at
        })

    # Fallback to single item or sample if user has 0-1 items
    if len(items_to_use) == 0:
        # Fallback to popular produce pair for instant demonstration
        items_to_use = [
            {"food_type": "banana", "scan_id": None, "shelf_life_days": 2},
            {"food_type": "apple", "scan_id": None, "shelf_life_days": 1},
        ]

    # 3. Generate Combined Recipe via Claude LLM or Local Culinary Synthesizer
    recipe_data = AgentRecipeService.generate_combined_recipe(items_to_use)

    # 4. Log the call in agent_recipe_logs
    try:
        log_entry = AgentRecipeLog(
            user_id=current_user.id,
            ingredients_used=json.dumps([it.get("food_type") for it in items_to_use]),
            recipe_title=recipe_data.get("recipe_title", "Zero-Waste Dish"),
            recipe_json=json.dumps(recipe_data)
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"[Agent Recipe] Failed to log call: {e}")

    calls_remaining = max(0, DAILY_AGENT_CALL_LIMIT - (calls_today_count + 1))
    recipe_data["calls_remaining_today"] = calls_remaining

    return recipe_data
