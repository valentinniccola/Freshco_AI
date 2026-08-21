from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from database import get_db
from models import PredictionRecord, User
from schemas import AnalyticsResponse, StatusBreakdown, StatusCounts, StatusPercentages, DailyTrendItem
from auth import get_current_user_optional

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])

@router.get("", response_model=AnalyticsResponse)
def get_analytics(
    range: str = Query("week", description="Time range: 'week' (7 days), 'month' (30 days), 'all' (all time)"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Returns analytics metrics computed via direct SQL aggregation:
    - Total scans in range
    - Fresh / Nearly Spoiled / Spoiled counts & percentages
    - Food wasted percentage: (Spoiled count / total scans) * 100
    - Time-series daily trend data grouped by DATE(created_at) and freshness_status
    """
    now = datetime.utcnow()
    start_date = None

    if range == "week":
        start_date = now - timedelta(days=7)
    elif range == "month":
        start_date = now - timedelta(days=30)
    elif range == "all":
        start_date = None
    else:
        raise HTTPException(status_code=400, detail="Invalid range. Must be 'week', 'month', or 'all'.")

    # 1. SQL Aggregation Query for Status Breakdown:
    # SELECT freshness_status, COUNT(id) as count FROM predictions WHERE ... GROUP BY freshness_status
    status_query = db.query(
        PredictionRecord.freshness_status,
        func.count(PredictionRecord.id).label("count")
    )
    if start_date:
        status_query = status_query.filter(PredictionRecord.created_at >= start_date)
    if current_user:
        status_query = status_query.filter(
            (PredictionRecord.user_id == current_user.id) | (PredictionRecord.user_id == None)
        )
    status_results = status_query.group_by(PredictionRecord.freshness_status).all()

    counts_map = {"Fresh": 0, "Nearly Spoiled": 0, "Spoiled": 0}
    for status_name, count in status_results:
        if status_name in counts_map:
            counts_map[status_name] = count
        elif "Uncertain" in status_name:
            counts_map["Nearly Spoiled"] += count

    total_scans = sum(counts_map.values())

    if total_scans > 0:
        fresh_pct = round((counts_map["Fresh"] / total_scans) * 100, 1)
        nearly_pct = round((counts_map["Nearly Spoiled"] / total_scans) * 100, 1)
        spoiled_pct = round((counts_map["Spoiled"] / total_scans) * 100, 1)
        wasted_pct = spoiled_pct
    else:
        fresh_pct = 0.0
        nearly_pct = 0.0
        spoiled_pct = 0.0
        wasted_pct = 0.0

    # 2. SQL Aggregation Query for Daily Time-Series Trend:
    # SELECT DATE(created_at) as scan_date, freshness_status, COUNT(id) as count FROM predictions GROUP BY DATE(created_at), freshness_status
    daily_query = db.query(
        func.date(PredictionRecord.created_at).label("scan_date"),
        PredictionRecord.freshness_status,
        func.count(PredictionRecord.id).label("count")
    )
    if start_date:
        daily_query = daily_query.filter(PredictionRecord.created_at >= start_date)
    if current_user:
        daily_query = daily_query.filter(
            (PredictionRecord.user_id == current_user.id) | (PredictionRecord.user_id == None)
        )
    
    daily_rows = daily_query.group_by(
        func.date(PredictionRecord.created_at),
        PredictionRecord.freshness_status
    ).order_by("scan_date").all()

    # Aggregate daily rows into time-series dictionaries
    trends_by_date: Dict[str, Dict[str, int]] = {}
    for scan_date, status_name, count in daily_rows:
        date_str = str(scan_date)
        if date_str not in trends_by_date:
            trends_by_date[date_str] = {"Fresh": 0, "Nearly_Spoiled": 0, "Spoiled": 0, "total": 0}
        
        if status_name == "Fresh":
            trends_by_date[date_str]["Fresh"] += count
        elif status_name == "Spoiled":
            trends_by_date[date_str]["Spoiled"] += count
        else:
            trends_by_date[date_str]["Nearly_Spoiled"] += count
            
        trends_by_date[date_str]["total"] += count

    daily_trends = [
        DailyTrendItem(
            date=d,
            Fresh=vals["Fresh"],
            Nearly_Spoiled=vals["Nearly_Spoiled"],
            Spoiled=vals["Spoiled"],
            total=vals["total"]
        )
        for d, vals in sorted(trends_by_date.items(), key=lambda x: x[0])
    ]

    return AnalyticsResponse(
        range=range,
        total_scans=total_scans,
        wasted_percentage=wasted_pct,
        status_breakdown=StatusBreakdown(
            counts=StatusCounts(
                Fresh=counts_map["Fresh"],
                Nearly_Spoiled=counts_map["Nearly Spoiled"],
                Spoiled=counts_map["Spoiled"]
            ),
            percentages=StatusPercentages(
                Fresh=fresh_pct,
                Nearly_Spoiled=nearly_pct,
                Spoiled=spoiled_pct
            )
        ),
        daily_trends=daily_trends
    )
