import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse, Message
from twilio.rest import Client
from dotenv import load_dotenv
from itertools import product
import numpy as np

pairings = {}
queue = []


def load_twilio_config():
    load_dotenv()
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    number = os.environ['TWILIO_NUMBER']

    if not all([account_sid, auth_token, number]):
        raise Exception

    return account_sid, auth_token, number


def load_model():
    model = {}
    with open("glove.6B.50d.txt", "r", encoding="utf-8") as file:
        for line in file.readlines():
            parts = line.split(' ')
            model[parts[0]] = np.array([float(x) for x in parts[1:]])

    return model


def cosine_similarity(word1, word2):
    global model
    vec1 = model[word1]
    vec2 = model[word2]
    return vec1.dot(vec2) / (np.linalg.norm(vec1, 2) * np.linalg.norm(vec2, 2))


account_sid, auth_token, number = load_twilio_config()
client = Client(account_sid, auth_token)
model = load_model()
app = Flask(__name__)


def is_queued(sender_number):
    return sender_number in queue


def is_active(sender_number):
    return sender_number in pairings


def send_message(message, recipient):
    client.messages.create(
        body=message,
        from_=number,
        to=recipient
    )
    return message


# A route to respond to SMS messages
@app.route('/sms', methods=['POST'])
def incoming():
    global pairings, queue
    data = request.form['Body']
    sender_number = request.form['From']

    n_keywords = 3
    split = data.split(" ")
    action = split[0]
    keywords = split[1:n_keywords+1]

    if is_active(sender_number):
        if action == "!quit":
            partner = pairings.pop(sender_number)
            pairings.pop(partner)

            send_message(
                f'{sender_number} disconnected! Reconnecting you to another match...',
                partner
            )

            return match(partner)
        else:
            partner = pairings[sender_number]
            send_message(f'{data}', partner)
    else:
        if action == "!start":
            match(sender_number, keywords)
        else:
            send_message(f'Not connected! Please enter !start to get matched...', sender_number)

    return None


def match(sender_number, keywords):
    global pairings, queue
    if is_queued(sender_number) or is_active(sender_number):
        pass
    else:
        most_compatible = (None, -np.inf)
        for (possibleMatch, targetInterests) in queue:
            for interest1, interest2 in product(keywords, targetInterests):
                score = cosine_similarity(interest1, interest2)
                if score > most_compatible[1]:
                    most_compatible = (possibleMatch, score)

        threshold = 0.6
        if most_compatible[1] > threshold:
            partner = most_compatible[0]
            send_message(
                f"You've been matched with {partner}!",
                sender_number
            )
            send_message(
                f"You've been matched with {sender_number}!",
                partner
            )
        else:
            queue.append(sender_number)
            send_message(f"Queued!", sender_number)

    return None


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
