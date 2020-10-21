
from flask import request, jsonify, Flask
import git
import os 
from flask_talisman import Talisman 
import time

import hmac
import hashlib

app = Flask(__name__) #run using "flask run --host 0.0.0.0:5000 #and note fals_app is an enriromen varabe and you need kill -9 to kill flask server. maybe nohup is needed
#Talisman(app) 
#GIT_USER=os.getenv("GIT_USER")
#GIT_PASS=os.getenv("GIT_PASS")
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
        print("pulling:",origin.pull()) #not supposed to affect local files we changed that are not changed on parent
        print("... with secret")
        os.environ["TIMEVERSION"]=str(int(time.time()))
        os.system('source .git/hooks/post-merge') 
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
    #print('signature=',x_hub_signature)
    #print("private key=",private_key)
    hash_algorithm, github_signature = x_hub_signature.split('=', 1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin-1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)
    
if __name__ == "__main__":
    app.run()#ssl_context=('cert.pem', 'key.pem'))