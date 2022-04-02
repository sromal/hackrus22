import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
import urllib
from twilio.rest import Client
from dotenv import load_dotenv

pairings = {}
queue = []

def load_twilio_config():
    load_dotenv()
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    number = os.environ['TWILIO_NUMBER']
    print([account_sid, auth_token, number])

    if not all([account_sid, auth_token, number]):
        raise Exception

    return account_sid, auth_token, number


account_sid, auth_token, number = load_twilio_config()
client = Client(account_sid, auth_token)
app = Flask(__name__)


# A route to respond to SMS messages
@app.route('/sms', methods=['POST'])
def incoming():
    global pairings, queue
    print("Received!")
    data = urllib.parse.quote(request.form['Body'])
    sender_number = request.form['From']

    if (data == "!start"):
        match(sender_number)
    elif (data == "!quit"):
        partner = pairings.pop(sender_number)
        pairings.pop(partner)

        client.messages.create(
            body=f'{sender_number} disconnected! Reconnecting you to another match...',
            from_=number,
            to=partner
        )

        match(partner)
    else:
        partner = pairings[sender_number]
        client.messages.create(
            body=f'{data}',
            from_=number,
            to=partner
        )

def match(sender_number):
    global pairings, queue
    if (queue):
        partner = queue.pop(0)
        pairings[sender_number] = partner
        pairings[partner] = number

        client.messages.create(
            body=f"You've been matched with {partner}!",
            from_=number,
            to=sender_number
        )

        client.messages.create(
            body=f"You've been matched with {sender_number}!",
            from_=number,
            to=partner
        )
    else:
        queue.append(sender_number)
        client.messages.create(
            body=f"Queued!",
            from_=number,
            to=sender_number
        )


def test():
    name = urllib.parse.quote(request.form['Body'])

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
