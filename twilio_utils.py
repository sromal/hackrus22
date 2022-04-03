import os
from dotenv import load_dotenv

def load_twilio_config():
    load_dotenv()
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    number = os.environ['TWILIO_NUMBER']

    if not all([account_sid, auth_token, number]):
        raise Exception

    return account_sid, auth_token, number
