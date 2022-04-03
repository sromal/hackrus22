from ml import *
from twilio_utils import *
from flask import Flask, request
from twilio.rest import Client
from itertools import product

pairings = {}
interests = {}
queue = []

account_sid, auth_token, number = load_twilio_config()
client = Client(account_sid, auth_token)
model = load_model()
app = Flask(__name__)


def send_message(message, recipient):
    client.messages.create(
        body=message,
        from_=number,
        to=recipient
    )
    return message


def is_queued(sender_number):
    return sender_number in queue


def is_active(sender_number):
    return sender_number in pairings


# A route to respond to SMS messages
@app.route('/sms', methods=['POST'])
def incoming():
    global pairings, queue, interests
    data = request.form['Body']
    sender_number = request.form['From']

    n_keywords = 3
    split = data.split(" ")
    action = "" if len(split) == 0 else split[0]
    
    if is_active(sender_number):
        if action == "!quit":
            partner = pairings.pop(sender_number)
            pairings.pop(partner)
            interests.pop(sender_number)

            send_message(
                f'You finished your conversation!',
                sender_number
            )

            send_message(
                f'{sender_number} disconnected! Reconnecting you to another match...',
                partner
            )

            return match(partner)
        else:
            partner = pairings[sender_number]
            send_message(f'{data}', partner)
    elif is_queued(sender_number):
        if (action == "!quit"):
            queue.remove(sender_number)
            interests.pop(sender_number)

            send_message(
                f'You were dequeued!',
                sender_number
            )
    else:
        if action == "!start":
            valid_terms = [term for term in split[1:] if term in model] if len(split) >= 2 else []
            keywords = valid_terms[:min(n_keywords, len(valid_terms))]

            interests[sender_number] = keywords
            match(sender_number)
        else:
            send_message(f'Not connected! Please enter !start to get matched...', sender_number)

    return ""


def match(sender_number):
    global pairings, queue
    if is_queued(sender_number) or is_active(sender_number):
        pass
    else:
        most_compatible = (None, -np.inf, "", "")
        chosenIndex = -1
        keywords = interests[sender_number]
        for i, possibleMatch in enumerate(queue):
            targetInterests = interests[possibleMatch]
            for interest1, interest2 in product(keywords, targetInterests):
                score = cosine_similarity(model, interest1, interest2)
                if score > most_compatible[1]:
                    most_compatible = (possibleMatch, score, interest1, interest2)
                    chosenIndex = i
            if (not targetInterests) and (not keywords):
                most_compatible = (possibleMatch, 1.0, "anything", "anything")
                chosenIndex = i
        print(chosenIndex, most_compatible)

        threshold = 0.6
        if most_compatible[1] > threshold:
            partner = queue.pop(chosenIndex)
            pairings[sender_number] = partner
            pairings[partner] = sender_number

            topics = "anything"
            if keywords:
                if most_compatible[2] == most_compatible[3]:
                    topics = most_compatible[2]
                else:
                    topics = most_compatible[2] + " and " + most_compatible[3]

            send_message(
                f"You've been matched with {partner} to talk about {topics}!",
                sender_number
            )
            send_message(
                f"You've been matched with {sender_number} to talk about {topics}!",
                partner
            )
        else:
            queue.append(sender_number)
            send_message(f"Queued!", sender_number)

    return ""


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
