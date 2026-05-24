"""Email sending helpers for TaskFlow OTP flows."""
from django.core.mail import send_mail
from django.conf import settings


def send_otp_email(user, otp_code, purpose):
    """Send a beautifully formatted OTP email."""

    subject_map = {
        "register":       "🔐 Verify your TaskFlow account",
        "password_reset": "🔑 Reset your TaskFlow password",
        "login":          "🔓 Your TaskFlow login code",
    }
    action_map = {
        "register":       "complete your registration",
        "password_reset": "reset your password",
        "login":          "sign in to your account",
    }

    subject = subject_map.get(purpose, "Your TaskFlow OTP")
    action  = action_map.get(purpose, "continue")

    message = f"""
Hi {user.first_name},

Your TaskFlow one-time password (OTP) to {action} is:

  ┌─────────────┐
  │  {otp_code}  │
  └─────────────┘

This code expires in {getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes.

If you did not request this, please ignore this email.

— The TaskFlow Team
"""

    html_message = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0d0d0f; color: #f0ede8; margin: 0; padding: 0; }}
    .wrapper {{ max-width: 480px; margin: 40px auto; background: #141418; border: 1px solid rgba(255,255,255,0.07); border-radius: 16px; overflow: hidden; }}
    .header {{ background: #1c1c22; padding: 28px 36px; border-bottom: 1px solid rgba(255,255,255,0.07); }}
    .logo {{ font-size: 22px; font-weight: 800; letter-spacing: -0.03em; color: #f0ede8; }}
    .logo span {{ color: #ffc150; }}
    .body {{ padding: 36px; }}
    h2 {{ font-size: 20px; font-weight: 700; margin: 0 0 8px; color: #f0ede8; }}
    p {{ font-size: 14px; color: #8a8799; line-height: 1.6; margin: 0 0 20px; }}
    .otp-box {{ background: #0d0d0f; border: 2px solid #ffc150; border-radius: 12px; padding: 24px; text-align: center; margin: 24px 0; }}
    .otp-code {{ font-size: 40px; font-weight: 800; letter-spacing: 12px; color: #ffc150; font-family: monospace; }}
    .otp-label {{ font-size: 12px; color: #4e4c5a; margin-top: 8px; text-transform: uppercase; letter-spacing: 0.08em; }}
    .expiry {{ background: rgba(255,193,80,0.08); border: 1px solid rgba(255,193,80,0.2); border-radius: 8px; padding: 12px 16px; font-size: 13px; color: #ffc150; text-align: center; }}
    .footer {{ padding: 20px 36px; border-top: 1px solid rgba(255,255,255,0.07); font-size: 12px; color: #4e4c5a; }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <div class="logo">Task<span>Flow</span></div>
    </div>
    <div class="body">
      <h2>Hi {user.first_name} 👋</h2>
      <p>Here is your one-time password to <strong style="color:#f0ede8">{action}</strong>. Enter it on the verification page to continue.</p>

      <div class="otp-box">
        <div class="otp-code">{otp_code}</div>
        <div class="otp-label">Your OTP code</div>
      </div>

      <div class="expiry">
        ⏱ This code expires in <strong>{getattr(settings, 'OTP_EXPIRY_MINUTES', 10)} minutes</strong>
      </div>

      <p style="margin-top:24px;font-size:13px;">If you did not request this, you can safely ignore this email. Your account remains secure.</p>
    </div>
    <div class="footer">
      This is an automated message from TaskFlow. Please do not reply to this email.
    </div>
  </div>
</body>
</html>
"""

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
