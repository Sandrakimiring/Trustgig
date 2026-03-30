import os, africastalking
from dotenv import load_dotenv

load_dotenv()
AT_USERNAME = os.getenv("AT_USERNAME", "sandbox")
AT_API_KEY = os.getenv("AT_API_KEY")

print(f"Testing AT Sandbox with username: {AT_USERNAME}")
africastalking.initialize(AT_USERNAME, AT_API_KEY)
sms = africastalking.SMS

phone = "+254797744542"
message = "TrustGig Sandbox Diagnostic Text 1"

try:
    response = sms.send(message, [phone])
    print("\nAPI Response:")
    print(response)
except Exception as e:
    print("\nAPI Exception:")
    print(str(e))
