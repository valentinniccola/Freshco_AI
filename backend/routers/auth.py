import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, PasswordResetCode
from schemas import (
    UserCreate, UserLogin, UserOut, Token,
    ForgotPasswordRequest, VerifyCodeRequest, ResetPasswordRequest, PasswordResetResponse
)
from auth import verify_password, get_password_hash, create_access_token, get_current_user
from email_service import EmailService
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if username or email already exists
    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    
    if existing_user:
        if existing_user.username == user_data.username:
            detail = "Username already taken. Please choose a different username."
        else:
            detail = "Email address is already registered. Please sign in instead."
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        phone_number=user_data.phone_number,
        hashed_password=hashed_pw
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(data={"sub": str(new_user.id), "username": new_user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": new_user
    }

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        (User.username == login_data.username_or_email) | (User.email == login_data.username_or_email)
    ).first()

    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.get("/me", response_model=UserOut)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/forgot-password/request", response_model=PasswordResetResponse)
def request_password_reset(req: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Generates a 6-digit verification code and sends it to the user's email via Gmail SMTP.
    Rate limited to max 3 requests per email per hour.
    """
    clean_email = req.email.lower().strip()

    # 1. Verify user exists
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please check your email or register."
        )

    # 2. Rate limiting check (max 3 requests per email per hour)
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent_requests_count = db.query(PasswordResetCode).filter(
        PasswordResetCode.email == clean_email,
        PasswordResetCode.created_at >= one_hour_ago
    ).count()

    if recent_requests_count >= settings.RESET_MAX_REQUESTS_PER_HOUR:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many password reset requests. Please wait a while before requesting a new code."
        )

    # 3. Invalidate any previously active codes for this email
    db.query(PasswordResetCode).filter(
        PasswordResetCode.email == clean_email,
        PasswordResetCode.used == False
    ).update({"used": True})

    # 4. Generate cryptographically secure 6-digit code
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.utcnow() + timedelta(minutes=settings.RESET_CODE_EXPIRE_MINUTES)

    reset_entry = PasswordResetCode(
        email=clean_email,
        code=code,
        expires_at=expires_at,
        used=False
    )
    db.add(reset_entry)
    db.commit()

    # 5. Send Email via Gmail SMTP
    sent = EmailService.send_password_reset_code(clean_email, code)
    if not sent:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            return PasswordResetResponse(
                message=f"Verification code generated (SMTP not configured). Code expires in {settings.RESET_CODE_EXPIRE_MINUTES} minutes.",
                email=clean_email
            )

    return PasswordResetResponse(
        message=f"A 6-digit verification code has been sent to {clean_email}. Please check your inbox and spam folder.",
        email=clean_email
    )

@router.post("/forgot-password/verify-code", response_model=PasswordResetResponse)
def verify_reset_code(req: VerifyCodeRequest, db: Session = Depends(get_db)):
    """
    Step 1 of Password Reset: Verifies the 6-digit code before unlocking the password reset form.
    """
    clean_email = req.email.lower().strip()
    clean_code = req.code.strip()

    reset_entry = db.query(PasswordResetCode).filter(
        PasswordResetCode.email == clean_email,
        PasswordResetCode.code == clean_code,
        PasswordResetCode.used == False
    ).order_by(PasswordResetCode.created_at.desc()).first()

    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code. Please check the 6-digit code or request a new one."
        )

    if reset_entry.expires_at < datetime.utcnow():
        reset_entry.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    return PasswordResetResponse(
        message="Code verified successfully. Please enter your new password.",
        email=clean_email
    )

@router.post("/forgot-password/reset", response_model=PasswordResetResponse)
def reset_password(req: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Step 2 of Password Reset: Sets the new Bcrypt-hashed password after verification.
    Invalidates the code immediately (single-use).
    """
    clean_email = req.email.lower().strip()
    clean_code = req.code.strip()

    # 1. Find matching reset code
    reset_entry = db.query(PasswordResetCode).filter(
        PasswordResetCode.email == clean_email,
        PasswordResetCode.code == clean_code,
        PasswordResetCode.used == False
    ).order_by(PasswordResetCode.created_at.desc()).first()

    if not reset_entry:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or already used verification code. Please request a new code."
        )

    # 2. Check Expiry
    if reset_entry.expires_at < datetime.utcnow():
        reset_entry.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code."
        )

    # 3. Find User
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account associated with this email was not found."
        )

    # 4. Hash and update new password
    user.hashed_password = get_password_hash(req.new_password)
    
    # 5. Invalidate code immediately (single-use)
    reset_entry.used = True
    db.commit()

    return PasswordResetResponse(
        message="Password has been reset successfully! You can now sign in with your new password.",
        email=clean_email
    )
