import africastalking
from pprint import pprint

try:
    africastalking.initialize('sandbox', 'atsk_cf4aa6ddb577c0c787d577fa961cda0022be779d9cd4825898c977c6536d868a6e73d498')
    sms = africastalking.SMS
    response = sms.send('Direct sandbox test via Python', ['+254797744542'])
    pprint(response)
except Exception as e:
    print('Error:', e)
