import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
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

def isQueued(sender_number):
    return sender_number in queue
def isActive(sender_number):
    return sender_number in pairings
def sendMessage(message, recipient):
    client.messages.create(
        body=message,
        from_=number,
        to=recipient
    )


# A route to respond to SMS messages
@app.route('/sms', methods=['POST'])
def incoming():
    global pairings, queue
    print("Received!")
    data = request.form['Body']
    sender_number = request.form['From']

    if data == "!start":
        match(sender_number)
    elif isActive(sender_number):
        if data == "!quit":
            partner = pairings.pop(sender_number)
            pairings.pop(partner)

            sendMessage(
                f'{sender_number} disconnected! Reconnecting you to another match...',
                partner
            )

            match(partner)
        else:
            partner = pairings[sender_number]
            sendMessage(f'{data}', partner)
    else:
        sendMessage(f'Not connected! Please enter !start to get matched...', sender_number)


def match(sender_number):
    global pairings, queue
    if isQueued(sender_number) or isActive(sender_number):
        pass
    elif queue:
        partner = queue.pop(0)
        pairings[sender_number] = partner
        pairings[partner] = sender_number

        sendMessage(
            f"You've been matched with {partner}!",
            sender_number
        )
        sendMessage(
            f"You've been matched with {sender_number}!",
            partner
        )
    else:
        queue.append(sender_number)
        sendMessage(f"Queued!", sender_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
