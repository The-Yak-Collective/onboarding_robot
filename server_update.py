
from flask import request, jsonify, Flask
import git
import os 
from flask_talisman import Talisman

import hmac
import hashlib

app = Flask(__name__) 
Talisman(app)
SERVER_UPDATE=os.getenv("SERVER_UPDATE")

@app.route('/update_robot', methods=['POST'])
def webhook():
    print("got update request")
    if request.method == 'POST':
        x_hub_signature = request.headers.get('X-Hub-Signature')
        if not is_valid_signature(x_hub_signature, request.data, SERVER_UPDATE):
            print("missing correct token/secret for server_update")
            return 'missing password', 400
        repo = git.Repo('.')
        print("repo:",repo)
        origin = repo.remotes.origin
        print("origin:",origin)
        origin.pull() #not supposed to affect local files we changed that are not changed on parent
        print("now with secret")
        return 'Updated robot successfully', 200
    else:
        return 'Wrong event type', 400

@app.route('/version', methods=['GET'])
def whatisversion():
    print("with Talisman?")
    return jsonify(os.getenv("TIMEVERSION"))

def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    print('signature=',x_hub_signature)
    print("private key=",private_key)
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)