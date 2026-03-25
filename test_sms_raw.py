import requests

url = "https://api.sandbox.africastalking.com/version1/messaging"
headers = {
    "apiKey": 'atsk_cf4aa6ddb577c0c787d577fa961cda0022be779d9cd4825898c977c6536d868a6e73d498',
    "Content-Type": "application/x-www-form-urlencoded",
    "Accept": "application/json"
}
data = {
    "username": "sandbox",
    "to": "+254797744542",
    "message": "Raw request SSL bypass test"
}

try:
    response = requests.post(url, headers=headers, data=data, verify=False)
    print("Status:", response.status_code)
    print("Response:", response.text)
except Exception as e:
    print('Error:', e)
