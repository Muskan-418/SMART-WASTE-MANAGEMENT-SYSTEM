# notify.py
# Simple notification stubs. Replace with real email/SMS/push providers in production.

import logging
from config import NOTIFY_EMAIL, NOTIFY_SMS_NUMBER

logger = logging.getLogger("notify")
logger.setLevel(logging.INFO)

def send_email(subject: str, body: str, to: str = NOTIFY_EMAIL):
    # Placeholder: integrate SMTP or cloud email (SES, SendGrid)
    logger.info(f"[EMAIL] To: {to} | Subject: {subject} | Body: {body}")
    # Example: use smtplib here in production

def send_sms(message: str, to: str = NOTIFY_SMS_NUMBER):
    # Placeholder: integrate Twilio or other SMS provider
    logger.info(f"[SMS] To: {to} | Msg: {message}")

def send_alert_for_bin(bin_meta: dict, level: float):
    subject = f"Bin {bin_meta.get('bin_code','?')} is {level:.1f}% full"
    body = f"Bin '{bin_meta.get('name')}' (code {bin_meta.get('bin_code')}) at {level:.1f}% fill requires collection."
    send_email(subject, body)
    send_sms(body)
