import africastalking
import os
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY  = os.getenv("AT_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8000")


def send_sms(phone: str, message: str) -> bool:
    if not AT_API_KEY:
        print(f"📱 [SMS MOCK] → {phone}: {message}")
        return False
    try:
        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        sms = africastalking.SMS
        response = sms.send(message, [phone])
        print(f"[SMS] → {phone} | {response}")
        return True
    except Exception as e:
        print(f"[SMS ERROR] {e}")
        return False


def send_match_sms(phone: str, job_title: str, budget: float, score: float, job_id: int = 0) -> bool:
    score_pct = int(score * 100)
    message = (
        f"New Gig Match!\n"
        f"{job_title}\n"
        f"Budget: KES {int(budget)}\n"
        f"Match: {score_pct}%\n\n"
        f"View job: {FRONTEND_URL}/trustgig_ui.html?job={job_id}\n\n"
        f"Reply 1 to apply, 2 to ignore"
    )
    return send_sms(phone, message)


def send_application_sms_to_client(phone: str, client_name: str, freelancer_name: str, job_title: str, job_id: int, score: float) -> bool:
    score_pct = int(score * 100)
    message = (
        f"Hello {client_name},\n"
        f"{freelancer_name} applied to your job:\n"
        f"'{job_title}'\n"
        f"Match score: {score_pct}%\n\n"
        f"To start work, fund escrow:\n"
        f"{FRONTEND_URL}/trustgig_ui.html?job={job_id}&action=fund\n\n"
        f"Reply YES to accept, NO to decline"
    )
    return send_sms(phone, message)


def send_escrow_funded_sms(phone: str, freelancer_name: str, job_title: str, amount: float, job_id: int) -> bool:
    message = (
        f"Great news {freelancer_name}!\n"
        f"Escrow of KES {int(amount)} funded for:\n"
        f"'{job_title}'\n\n"
        f"You can now start work.\n"
        f"View job: {FRONTEND_URL}/trustgig_ui.html?job={job_id}"
    )
    return send_sms(phone, message)


def send_work_done_sms_to_client(phone: str, client_name: str, freelancer_name: str, job_title: str, amount: float, job_id: int) -> bool:
    message = (
        f"Hello {client_name},\n"
        f"{freelancer_name} has completed:\n"
        f"'{job_title}'\n\n"
        f"Release KES {int(amount)} payment:\n"
        f"{FRONTEND_URL}/trustgig_ui.html?job={job_id}&action=release\n\n"
        f"Reply RELEASE to pay the freelancer"
    )
    return send_sms(phone, message)


def send_payment_released_sms(phone: str, name: str, amount: float, job_title: str) -> bool:
    message = (
        f"Hello {name},\n"
        f"KES {int(amount)} for '{job_title}' "
        f"is being sent to your M-Pesa.\n"
        f"You will receive an M-Pesa confirmation shortly.\n\n"
        f"Thank you for using TrustGig!"
    )
    return send_sms(phone, message)


def send_mpesa_disbursement(phone: str, name: str, amount: float, job_title: str) -> bool:
    """Trigger actual M-Pesa B2C payment via Africa's Talking."""
    if not AT_API_KEY:
        print(f"💸 [MPESA MOCK] → {phone}: KES {amount}")
        return False
    try:
        africastalking.initialize(AT_USERNAME, AT_API_KEY)
        payments = africastalking.Payment
        recipients = [{
            "phoneNumber": phone,
            "amount": amount,
            "currencyCode": "KES",
            "name": name,
            "metadata": {"job": job_title}
        }]
        response = payments.mobileB2C(
            productName="TrustGig",
            recipients=recipients
        )
        print(f"[MPESA] → {phone}: KES {amount} | {response}")
        return True
    except Exception as e:
        print(f"[MPESA ERROR] {e}")
        return False