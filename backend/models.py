from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    phone_number = Column(String(25), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    predictions = relationship("PredictionRecord", back_populates="user", cascade="all, delete-orphan")


class PasswordResetCode(Base):
    __tablename__ = "password_reset_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), index=True, nullable=False)
    code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    image_path = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    food_category = Column(String(50), default="General")
    
    # Classification results
    freshness_status = Column(String(50), nullable=False)  # "Fresh", "Nearly Spoiled", "Spoiled"
    confidence_score = Column(Float, nullable=False)        # 0.0 - 1.0 (e.g. 0.94)
    probabilities_json = Column(Text, nullable=False)       # JSON string {"Fresh": 0.94, "Nearly Spoiled": 0.04, "Spoiled": 0.02}
    
    # Shelf life & storage insights
    shelf_life_days = Column(Integer, default=0)
    shelf_life_desc = Column(String(255), nullable=True)
    storage_advice = Column(Text, nullable=True)
    defect_metrics_json = Column(Text, nullable=True)       # JSON string for OpenCV visual analysis metrics
    
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="predictions")
