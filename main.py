import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import urllib
from twilio.rest import Client
from dotenv import load_dotenv


def load_twilio_config():
    load_dotenv()
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    number = os.environ['TWILIO_NUMBER']

    if not all([account_sid, auth_token, number]):
        raise Exception

    return account_sid, auth_token, number


account_sid, auth_token, number = load_twilio_config()
client = Client(account_sid, auth_token)
app = Flask(__name__)


# A route to respond to SMS messages
@app.route('/sms', methods=['POST'])
def test():
    name = request.form['Body']

    # Get the sender's number
    sender_number = request.form['From']

    # Add sender's number to numbers to be notified
    # numbers.append(sender_number)

    message = client.messages.create(
        body=f'Hello {name}!',
        from_=number,
        to=sender_number
    )

    return message.body


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
