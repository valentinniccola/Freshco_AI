import json
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import User, PredictionRecord, AdminLog
from schemas import (
    AdminStatsResponse, AdminUserSummary, AdminUserDetail,
    AdminUserStatusUpdateRequest, AdminLogResponse, HistoryItem
)
from auth import get_current_admin_user

router = APIRouter(prefix="/api/admin", tags=["Admin Dashboard"])

@router.get("/stats", response_model=AdminStatsResponse)
def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Platform-wide aggregate metrics for the Admin Dashboard.
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    disabled_users = total_users - active_users

    total_scans = db.query(PredictionRecord).count()

    fresh_count = db.query(PredictionRecord).filter(PredictionRecord.freshness_status == "Fresh").count()
    nearly_spoiled_count = db.query(PredictionRecord).filter(PredictionRecord.freshness_status == "Nearly Spoiled").count()
    spoiled_count = db.query(PredictionRecord).filter(PredictionRecord.freshness_status == "Spoiled").count()

    platform_fresh_pct = round((fresh_count / total_scans * 100), 1) if total_scans > 0 else 0.0
    platform_nearly_spoiled_pct = round((nearly_spoiled_count / total_scans * 100), 1) if total_scans > 0 else 0.0
    platform_spoiled_pct = round((spoiled_count / total_scans * 100), 1) if total_scans > 0 else 0.0

    total_waste_prevented = fresh_count + nearly_spoiled_count

    return {
        "total_users": total_users,
        "active_users": active_users,
        "disabled_users": disabled_users,
        "total_scans_platform": total_scans,
        "platform_fresh_pct": platform_fresh_pct,
        "platform_nearly_spoiled_pct": platform_nearly_spoiled_pct,
        "platform_spoiled_pct": platform_spoiled_pct,
        "total_waste_prevented_est": total_waste_prevented,
    }

@router.get("/users", response_model=List[AdminUserSummary])
def get_admin_users(
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    List of all registered users with scan counts, status, and registration dates.
    Passwords and hashes are completely omitted.
    """
    query = db.query(User)

    if search:
        s = f"%{search.strip().lower()}%"
        query = query.filter((User.username.ilike(s)) | (User.email.ilike(s)))

    if status_filter == "active":
        query = query.filter(User.is_active == True)
    elif status_filter == "disabled":
        query = query.filter(User.is_active == False)

    users = query.order_by(User.created_at.desc()).all()

    # Pre-calculate scan counts for all users
    scan_counts = dict(
        db.query(PredictionRecord.user_id, func.count(PredictionRecord.id))
        .filter(PredictionRecord.user_id.isnot(None))
        .group_by(PredictionRecord.user_id)
        .all()
    )

    results = []
    for u in users:
        results.append(AdminUserSummary(
            id=u.id,
            username=u.username,
            email=u.email,
            phone_number=u.phone_number,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
            last_login=u.last_login,
            total_scans=scan_counts.get(u.id, 0)
        ))

    return results

@router.get("/users/{user_id}", response_model=AdminUserDetail)
def get_admin_user_detail(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Detailed profile and complete scan history for an individual user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    scans = (
        db.query(PredictionRecord)
        .filter(PredictionRecord.user_id == user_id)
        .order_by(PredictionRecord.created_at.desc())
        .all()
    )

    history_items = []
    for s in scans:
        food_type = "food item"
        try:
            if s.defect_metrics_json:
                metrics_data = json.loads(s.defect_metrics_json)
                food_type = metrics_data.get("food_type", s.food_category)
        except Exception:
            food_type = s.food_category

        history_items.append(HistoryItem(
            id=s.id,
            image_url=s.image_path,
            original_filename=s.original_filename,
            food_category=s.food_category,
            food_type=food_type,
            freshness_status=s.freshness_status,
            confidence_score=s.confidence_score,
            shelf_life_days=s.shelf_life_days,
            shelf_life_desc=s.shelf_life_desc,
            storage_advice=s.storage_advice,
            created_at=s.created_at
        ))

    user_summary = AdminUserSummary(
        id=user.id,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        total_scans=len(history_items)
    )

    return {
        "user": user_summary,
        "scans": history_items
    }

@router.patch("/users/{user_id}/status", response_model=AdminUserSummary)
def update_user_status(
    user_id: int,
    req: AdminUserStatusUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Enable or disable a user account.
    Logs the action in admin_logs for accountability.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found."
        )

    if user.id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot disable their own account."
        )

    old_status = user.is_active
    user.is_active = req.is_active
    
    action_name = "ENABLE_USER" if req.is_active else "DISABLE_USER"
    log_entry = AdminLog(
        admin_id=admin_user.id,
        action=action_name,
        target_user_id=user.id,
        details=f"Admin '{admin_user.username}' changed user '{user.username}' active status from {old_status} to {req.is_active}. Reason: {req.reason or 'Manual admin update.'}"
    )
    db.add(log_entry)
    db.commit()
    db.refresh(user)

    total_scans = db.query(PredictionRecord).filter(PredictionRecord.user_id == user.id).count()

    return AdminUserSummary(
        id=user.id,
        username=user.username,
        email=user.email,
        phone_number=user.phone_number,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
        last_login=user.last_login,
        total_scans=total_scans
    )

@router.get("/logs", response_model=List[AdminLogResponse])
def get_admin_logs(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_admin_user)
):
    """
    Retrieves administrative audit logs.
    """
    logs = (
        db.query(AdminLog)
        .order_by(AdminLog.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []
    for l in logs:
        results.append(AdminLogResponse(
            id=l.id,
            admin_id=l.admin_id,
            admin_username=l.admin.username if l.admin else f"Admin #{l.admin_id}",
            action=l.action,
            target_user_id=l.target_user_id,
            target_username=l.target_user.username if l.target_user else None,
            details=l.details,
            created_at=l.created_at
        ))

    return results
