import re
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, EmailStr, field_validator

# Auth Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    phone_number: Optional[str] = None

    @field_validator("phone_number")
    def validate_phone(cls, v):
        if v is not None and v.strip() != "":
            cleaned = re.sub(r'[\s\-\(\)\.]', '', v)
            if not re.match(r'^\+?[0-9]{7,15}$', cleaned):
                raise ValueError("Invalid phone number format. Please provide a valid phone number (e.g. +1 555-123-4567 or 9876543210).")
            return v.strip()
        return None

class UserLogin(BaseModel):
    username_or_email: str
    password: str

class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    phone_number: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

class TokenData(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None

# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class VerifyCodeRequest(BaseModel):
    email: EmailStr
    code: str

    @field_validator("code")
    def validate_code(cls, v):
        v = v.strip()
        if not re.match(r'^[0-9]{6}$', v):
            raise ValueError("Verification code must be a 6-digit number.")
        return v

class ResetPasswordRequest(BaseModel):
    email: EmailStr
    code: str
    new_password: str

    @field_validator("code")
    def validate_code(cls, v):
        v = v.strip()
        if not re.match(r'^[0-9]{6}$', v):
            raise ValueError("Verification code must be a 6-digit number.")
        return v

    @field_validator("new_password")
    def validate_password_length(cls, v):
        if len(v) < 6:
            raise ValueError("New password must be at least 6 characters long.")
        return v

class PasswordResetResponse(BaseModel):
    message: str
    email: Optional[str] = None


# AI & Prediction Schemas
class DefectMetrics(BaseModel):
    discoloration_index: float
    spot_coverage_pct: float
    surface_homogeneity: float
    browning_score: float

class Probabilities(BaseModel):
    Fresh: float
    Nearly_Spoiled: float
    Spoiled: float

class RecipeSuggestion(BaseModel):
    title: str
    description: str
    prep_time: str
    source_url: str
    difficulty: str

class PredictionResponse(BaseModel):
    id: Optional[int] = None
    image_url: str
    original_filename: str
    food_category: str
    food_type: str = "food item"
    
    # Primary Prediction & Confidence Format
    freshness: str = "Fresh"               # e.g. "Nearly Spoiled"
    confidence: float = 0.95              # e.g. 0.78
    all_probabilities: Dict[str, float] = {} # e.g. {"Fresh": 0.15, "Nearly Spoiled": 0.78, "Spoiled": 0.07}

    freshness_status: str
    confidence_score: float
    probabilities: Probabilities
    shelf_life_days: int
    shelf_life_desc: str
    storage_advice: str
    defect_metrics: DefectMetrics
    action_recommendation: str
    
    # Recipe Suggestions (populated for Nearly Spoiled)
    recipe_suggestions: Optional[List[RecipeSuggestion]] = None
    
    # Output-Level Verification Flags
    is_uncertain: bool = False
    is_low_confidence: bool = False
    candidate_classes: List[str] = []
    status_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class HistoryItem(BaseModel):
    id: int
    image_url: str
    original_filename: str
    food_category: str
    freshness_status: str
    confidence_score: float
    shelf_life_days: int
    shelf_life_desc: Optional[str]
    storage_advice: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    total: int

class StatsResponse(BaseModel):
    total_scans: int
    fresh_count: int
    nearly_spoiled_count: int
    spoiled_count: int
    avg_confidence: float
    most_scanned_category: str


# Analytics Schemas
class StatusCounts(BaseModel):
    Fresh: int
    Nearly_Spoiled: int
    Spoiled: int

class StatusPercentages(BaseModel):
    Fresh: float
    Nearly_Spoiled: float
    Spoiled: float

class StatusBreakdown(BaseModel):
    counts: StatusCounts
    percentages: StatusPercentages

class DailyTrendItem(BaseModel):
    date: str
    Fresh: int
    Nearly_Spoiled: int
    Spoiled: int
    total: int

class AnalyticsResponse(BaseModel):
    range: str
    total_scans: int
    wasted_percentage: float
    status_breakdown: StatusBreakdown
    daily_trends: List[DailyTrendItem]
