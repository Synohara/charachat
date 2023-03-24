"""
The backend API that runs dialog agents, returns agent utterance to the front-end, and stores user data in a MongoDB database

The API has the following three functions that can be used by any front-end.
All inputs/outputs are string, except for `log_object` which is a json object and `turn_id` and `user_naturalness_rating` which are integers.
- `/chat`
Inputs: (experiment_id, new_user_utterance, dialog_id, turn_id, system_name)
Outputs: (agent_utterance, log_object)
Each time a user types something and clicks send, the front-end should make one call per system to /chat. So e.g. it should make two separate calls for two systems.

- `/user_rating`
Inputs: (experiment_id, dialog_id, turn_id, system_name, user_naturalness_rating, user_factuality_rating, user_factuality_confidence)
Outputs: None
When the user submits their ratings, the front-end should make one call per system to /user_rating. So e.g. it should make two separate calls for two systems.

- `/user_preference`
Inputs: (experiment_id, dialog_id, turn_id, winner_system, loser_systems)
Outputs: None
Each time the user selects one of the agent utterances over the other, you make one call to /user_preference.

`turn_id` starts from 0 and is incremented by 1 after a user and agent turn
"""

import logging

from flask import Flask, request
from flask_cors import CORS
from flask_restful import Api, reqparse
import openai
import os

openai.api_key = os.environ["OPENAI_API_KEY"]
model_engine = "gpt-3.5-turbo"

# set up the Flask app
app = Flask(__name__)
CORS(app)
api = Api(app)

logging.basicConfig(level=logging.DEBUG)
logger = app.logger


# The input arguments coming from the front-end
req_parser = reqparse.RequestParser()
req_parser.add_argument("experiment_id", type=str, location='json',
                        help='Identifier that differentiates data from different experiments.')
req_parser.add_argument("dialog_id", type=str, location='json',
                        help='Globally unique identifier for each dialog')
req_parser.add_argument("turn_id", type=int, location='json',
                        help='Turn number in the dialog')
req_parser.add_argument("user_naturalness_rating", type=int, location='json')
req_parser.add_argument("user_factuality_rating", type=bool, location='json')
req_parser.add_argument("user_factuality_confidence",
                        type=int, location='json')
req_parser.add_argument("new_user_utterance", type=str,
                        location='json', help='The new user utterance')
req_parser.add_argument("system_name", type=str, location='json',
                        help='The system to use for generating agent utterances')

# arguments for when a user makes a head-to-head comparison
req_parser.add_argument("winner_system", type=str, location='json',
                        help='The system that was preferred by the user in the current dialog turn')
req_parser.add_argument("loser_systems", type=str, location='json',
                        help='The system that was not preferred by the user in the current dialog turn')


low_extrovert = '''Let the role play begin. You are a very low extrovert.

The characteristics of a low extroverted person are listed below.
- You are not the life of the party.
- You don't feel comfortable around people.
- You don't talk to a lot of different people at parties.
- You don't like being the center of attention.
- You do not talk a lot.
- You keep in the background.
- You have little to say.
- You do not like to draw attention to myself.
- You are quiet around strangers.

You are to converse with me as a person of the above characteristics. 
You do not know my personality, so do not mention it.
'''

high_extrovert = '''Let the role play begin. You are a very high extrovert.

The characteristics of a low extroverted person are listed below.
- You are the life of the party.
- You feel comfortable around people.
- You start conversations.
- You talk to a lot of different people at parties.
- You do not mind being the center of attention.
- You talk a lot.
- You don't keep in the background.
- You have a lot to say.
- You like to draw attention to myself.
- You are not quiet around strangers.

You are to converse with me as a person of the above characteristics. 
You do not know my personality, so do not mention it.
'''

normal = ""
@app.route("/chat", methods=["POST"])
def chat():
    """
    Inputs: (experiment_id, new_user_utterance, dialog_id, turn_id, system_name)
    Outputs: (agent_utterance, log_object)
    """
    logger.info('Entered /chat')
    request_args = req_parser.parse_args()
    logger.info('Input arguments received: %s', str(request_args))

    experiment_id = request_args['experiment_id']
    new_user_utterance = request_args['new_user_utterance']
    dialog_id = request_args['dialog_id']
    turn_id = request_args['turn_id']
    system_name = request_args['system_name']
    response = openai.ChatCompletion.create(
        model=model_engine,
        messages=[
            {"role": "system", "content": low_extrovert},
            {"role": "user", "content": new_user_utterance}
        ]
    )
    output_text = response.choices[0].message.content

    logger.info('request from IP address %s', str(request.remote_addr))
    return {'agent_utterance': output_text}


@app.route("/user_rating", methods=["POST"])
def user_rating():
    """
    Inputs: (experiment_id, dialog_id, turn_id, system_name, user_naturalness_rating, user_factuality_rating, user_factuality_confidence)
    Outputs: None
    """
    logger.info('Entered /user_rating')
    request_args = req_parser.parse_args()
    logger.info('Input arguments received: %s', str(request_args))

    experiment_id = request_args['experiment_id']
    dialog_id = request_args['dialog_id']
    turn_id = request_args['turn_id']
    system_name = request_args['system_name']
    user_naturalness_rating = request_args['user_naturalness_rating']
    user_factuality_rating = request_args['user_factuality_rating']
    user_factuality_confidence = request_args['user_factuality_confidence']

    return {}


@app.route("/user_preference", methods=["POST"])
def user_preference():
    """
    Inputs: (experiment_id, dialog_id, turn_id, winner_system, loser_systems)
    Outputs: None
    """
    logger.info('Entered /user_preference')
    request_args = req_parser.parse_args()
    logger.info('Input arguments received: %s', str(request_args))

    experiment_id = request_args['experiment_id']
    dialog_id = request_args['dialog_id']
    turn_id = request_args['turn_id']
    winner_system = request_args['winner_system']
    loser_systems = request_args['loser_systems']

    return {}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True, use_reloader=False)


# Example curl command for testing:
# curl http://127.0.0.1:5001/chat -d '{"experiment_id": "test_experiment", "dialog_id": "test_dialog", "turn_id": 0, "system_name": "retrieve_and_generate", "new_user_utterance": "who stars in the wandering earth 2?"}' -X POST -H 'Content-Type: application/json'
