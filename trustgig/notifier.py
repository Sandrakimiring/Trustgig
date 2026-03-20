import os
import requests
import urllib3
from dotenv import load_dotenv

load_dotenv()

# Disable SSL warnings for sandbox (network proxy issue)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Africa's Talking configuration
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY")
AT_SMS_URL = "https://api.sandbox.africastalking.com/version1/messaging"

# Use live URL if not sandbox
if AT_USERNAME != "sandbox":
    AT_SMS_URL = "https://api.africastalking.com/version1/messaging"


def format_sms(job_title: str, budget: float, score: float) -> str:
    score_percent = int(score * 100)
    message = (
        f"New Gig Match!\n"
        f"{job_title}\n"
        f"Budget: ${int(budget)}\n"
        f"Match: {score_percent}%\n\n"
        f"Reply 1 to apply\n"
        f"Reply 2 to ignore"
    )
    return message


def send_match_sms(phone: str, job_title: str, budget: float, score: float) -> bool:
    try:
        message = format_sms(job_title, budget, score)

        headers = {
            "apiKey": AT_API_KEY,
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }

        data = {
            "username": AT_USERNAME,
            "to": phone,
            "message": message
        }

        response = requests.post(
            AT_SMS_URL,
            headers=headers,
            data=data,
            verify=False,  # Bypass SSL issues on restricted networks
            timeout=30
        )

        print(f"[SMS] Sent to {phone} | Status: {response.status_code}")
        print(f"[SMS] Response: {response.text}")

        return response.status_code == 201

    except Exception as e:
        print(f"[SMS ERROR] Failed to send to {phone}: {str(e)}")
        return False
