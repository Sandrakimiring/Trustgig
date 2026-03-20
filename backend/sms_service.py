"""
services/sms_service.py
────────────────────────
Africa's Talking SMS integration.
Set AT_API_KEY in .env to switch from mock to live.
"""

import logging
import os
from app.config import settings

logger = logging.getLogger(__name__)


def send_sms(phone: str, message: str) -> dict:
    """Send an SMS. Mocked when AT_API_KEY is not set."""
    if not settings.at_api_key:
        logger.info(f"[SMS MOCK] → {phone}: {message}")
        print(f"📱 [SMS MOCK] → {phone}\n   {message}\n")
        return {"status": "mocked", "phone": phone}

    try:
        import africastalking
        africastalking.initialize(settings.at_username, settings.at_api_key)
        sms = africastalking.SMS
        sender = settings.at_sender_id or None
        response = sms.send(message, [phone], sender)
        logger.info(f"[SMS SENT] → {phone} | {response}")
        return {"status": "sent", "response": response}
    except Exception as e:
        logger.error(f"[SMS ERROR] {e}")
        return {"status": "error", "error": str(e)}
def sms_new_match(freelancer_name: str, job_title: str, budget: float, job_id: int) -> str:
    return (
        f"Hello {freelancer_name}!\n"
        f"A job matching your skills was found.\n\n"
        f"Job: {job_title}\n"
        f"Budget: KES {budget:,.0f}\n\n"
        f"Apply: {settings.frontend_url}/jobs/{job_id}"
    )


def sms_application_accepted(freelancer_name: str, job_title: str) -> str:
    return (
        f"Congratulations {freelancer_name}!\n"
        f"Your application for '{job_title}' has been accepted.\n"
        f"Escrow will be funded shortly. Get ready to start!"
    )


def sms_escrow_funded(client_name: str, job_title: str, amount: float) -> str:
    return (
        f"Hello {client_name},\n"
        f"Escrow of KES {amount:,.0f} has been funded for '{job_title}'.\n"
        f"Work can now begin!"
    )


def sms_payment_released(freelancer_name: str, amount: float, job_title: str) -> str:
    return (
        f"Hello {freelancer_name},\n"
        f"Payment of KES {amount:,.0f} for '{job_title}' is on its way to your M-Pesa.\n"
        f"Thank you for using GigPlatform!"
    )