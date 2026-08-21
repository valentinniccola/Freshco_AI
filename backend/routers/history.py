from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import PredictionRecord, User
from schemas import HistoryItem, HistoryResponse, StatsResponse
from auth import get_current_user_optional

router = APIRouter(prefix="/api/history", tags=["Prediction History"])

@router.get("", response_model=HistoryResponse)
def get_prediction_history(
    status_filter: Optional[str] = Query(None, description="Filter by status: Fresh, Nearly Spoiled, Spoiled"),
    search: Optional[str] = Query(None, description="Search by filename or category"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    query = db.query(PredictionRecord)
    
    if current_user:
        query = query.filter((PredictionRecord.user_id == current_user.id) | (PredictionRecord.user_id == None))
    
    if status_filter and status_filter.lower() != "all":
        query = query.filter(PredictionRecord.freshness_status.ilike(f"%{status_filter}%"))

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (PredictionRecord.original_filename.ilike(search_pattern)) | 
            (PredictionRecord.food_category.ilike(search_pattern))
        )

    total = query.count()
    records = query.order_by(PredictionRecord.created_at.desc()).offset(offset).limit(limit).all()

    items = [
        HistoryItem(
            id=r.id,
            image_url=r.image_path,
            original_filename=r.original_filename,
            food_category=r.food_category,
            freshness_status=r.freshness_status,
            confidence_score=r.confidence_score,
            shelf_life_days=r.shelf_life_days,
            shelf_life_desc=r.shelf_life_desc,
            storage_advice=r.storage_advice,
            created_at=r.created_at
        )
        for r in records
    ]

    return HistoryResponse(items=items, total=total)

@router.get("/stats", response_model=StatsResponse)
def get_history_stats(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    query = db.query(PredictionRecord)
    if current_user:
        query = query.filter((PredictionRecord.user_id == current_user.id) | (PredictionRecord.user_id == None))
        
    all_records = query.all()
    total_scans = len(all_records)
    
    if total_scans == 0:
        return StatsResponse(
            total_scans=0,
            fresh_count=0,
            nearly_spoiled_count=0,
            spoiled_count=0,
            avg_confidence=0.0,
            most_scanned_category="None"
        )

    fresh_count = sum(1 for r in all_records if r.freshness_status == "Fresh")
    nearly_spoiled_count = sum(1 for r in all_records if r.freshness_status == "Nearly Spoiled")
    spoiled_count = sum(1 for r in all_records if r.freshness_status == "Spoiled")
    avg_confidence = round(sum(r.confidence_score for r in all_records) / total_scans * 100, 1)

    # Most scanned category
    category_counts = {}
    for r in all_records:
        category_counts[r.food_category] = category_counts.get(r.food_category, 0) + 1
    most_scanned = max(category_counts, key=category_counts.get) if category_counts else "General"

    return StatsResponse(
        total_scans=total_scans,
        fresh_count=fresh_count,
        nearly_spoiled_count=nearly_spoiled_count,
        spoiled_count=spoiled_count,
        avg_confidence=avg_confidence,
        most_scanned_category=most_scanned
    )

@router.delete("/{record_id}")
def delete_history_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    record = db.query(PredictionRecord).filter(PredictionRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Scan record not found.")
        
    db.delete(record)
    db.commit()
    return {"message": "Record deleted successfully", "id": record_id}

@router.delete("")
def clear_all_history(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    if current_user:
        db.query(PredictionRecord).filter(
            (PredictionRecord.user_id == current_user.id) | (PredictionRecord.user_id == None)
        ).delete(synchronize_session=False)
    else:
        db.query(PredictionRecord).delete(synchronize_session=False)
        
    db.commit()
    return {"message": "Scan history cleared successfully"}
