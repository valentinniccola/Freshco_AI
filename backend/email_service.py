import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import settings

class EmailService:
    @staticmethod
    def send_password_reset_code(recipient_email: str, code: str) -> bool:
        """
        Sends a 6-digit verification code to the recipient's email address via Gmail SMTP.
        """
        smtp_user = settings.SMTP_USER.strip() if settings.SMTP_USER else ""
        smtp_password = settings.SMTP_PASSWORD.strip() if settings.SMTP_PASSWORD else ""

        # Check if SMTP credentials are configured
        if not smtp_user or not smtp_password:
            print(f"[EmailService Notice] SMTP credentials not configured in .env. Password reset email skipped.")
            # If SMTP is not yet configured, return False so caller can return a clear message or development note
            return False

        subject = f"Your Freshco AI Verification Code: {code}"
        
        # HTML Email Template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="utf-8">
          <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #1e293b; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 32px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }}
            .header {{ text-align: center; margin-bottom: 24px; }}
            .brand {{ font-size: 24px; font-weight: 800; color: #10b981; letter-spacing: -0.5px; }}
            .title {{ font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 8px; }}
            .desc {{ font-size: 14px; color: #64748b; line-height: 1.5; margin-bottom: 24px; }}
            .code-box {{ background: #f0fdf4; border: 2px dashed #10b981; border-radius: 12px; padding: 18px; text-align: center; margin: 24px 0; }}
            .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 8px; color: #047857; margin: 0; font-family: monospace; }}
            .expiry-note {{ font-size: 12px; color: #ef4444; font-weight: 600; margin-top: 8px; }}
            .footer {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
            .security-tip {{ background: #fef2f2; border-radius: 8px; padding: 12px; font-size: 12px; color: #991b1b; line-height: 1.4; margin-top: 16px; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <div class="brand">🌿 Freshco AI</div>
              <div class="title">Password Reset Verification</div>
            </div>
            <p class="desc">
              We received a request to reset your password for your Freshco AI account. Use the 6-digit verification code below to complete the reset process:
            </p>
            
            <div class="code-box">
              <div class="otp-code">{code}</div>
              <div class="expiry-note">⏱️ Code expires in {settings.RESET_CODE_EXPIRE_MINUTES} minutes</div>
            </div>
            
            <div class="security-tip">
              <strong>Security Notice:</strong> Never share this code with anyone. Freshco AI staff will never ask for your verification code.
            </div>
            
            <div class="footer">
              If you did not request this password reset, please ignore this email. Your password will remain unchanged.<br><br>
              &copy; 2026 Freshco AI Food Freshness Detection
            </div>
          </div>
        </body>
        </html>
        """

        text_body = f"""
        Freshco AI Password Reset Verification

        Your 6-digit verification code is: {code}

        This code will expire in {settings.RESET_CODE_EXPIRE_MINUTES} minutes.
        If you did not request a password reset, please ignore this email.
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.EMAILS_FROM_NAME} <{smtp_user}>"
        msg["To"] = recipient_email

        msg.attach(MIMEText(text_body, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        try:
            # Connect via STARTTLS on port 587
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipient_email, msg.as_string())
            print(f"[EmailService] Verification code successfully sent to: {recipient_email}")
            return True
        except Exception as e:
            print(f"[EmailService Error] Failed to send email via SMTP: {e}")
            return False
