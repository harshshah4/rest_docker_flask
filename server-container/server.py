from flask import Flask, request, jsonify
import json
import logging
from queue import Queue

logging.basicConfig(filename='server.log', level=logging.DEBUG)


# helper class that helps creating two a singleton queue
class Helper:
    queue = Queue()
    queue_1 = Queue()

    def __init__(self):
        pass

    @staticmethod
    def get_queue():
        return Helper.queue

    @staticmethod
    def get_queue_1():
        return Helper.queue_1


# structure of each authenticated
class CameraAuthenticated(object):
    def __init__(self, uid, username, password):
        self.uid = uid
        self.username = username
        self.password = password


# Generic method to create response
def response_create(data, status_code):
    logging.info("status code is %s", str(status_code))
    return app.response_class(
        response=json.dumps(data),
        status=status_code,
        mimetype='application/json'
    )


# read the username and password file, required to provide auth token. There are safer ways like using encrypted db
def read_userPass_file():
    cameraAuthenticated = []
    user_pass_file = 'username-password.json'
    with open(user_pass_file) as json_file:
        logging.debug("file %s opened to read password and username", user_pass_file)
        data = json.load(json_file)
        for p in data['userPass']:
            uid = p['uid']
            password = p['password']
            username = p['username']
            cameraAuthenticated.append(CameraAuthenticated(uid, username, password))
    logging.debug("done reading password file")
    return cameraAuthenticated


user = read_userPass_file()
username_table = {u.username: u for u in user}
app = Flask(__name__)


# Fetch auth token for the response of session api
def authenticate(username, password):
    user_fetched = username_table.get(username, None)
    if user_fetched and user_fetched.password == password:
        logging.info("able to fetch auth token, authentic camera client")
        return user_fetched.uid
    logging.warning("unable to fetch auth token, not an authentic camera client")
    return None


# verify if the user is authenticated to run private APIs.
def verify(auth):
    entity = "user"
    with open('auth.json') as json_file:
        logging.debug("found auth file for validating the client to run private APIs")
        data = json.load(json_file)
        for p in data['auth']:
            if auth in p:
                logging.debug("found authentic camera client")
                entity = p[auth]
                break
    return entity


# fetch the auth token for the user authentication for later APIs. Used to differentiate camera with user
@app.route('/session', methods=['POST'])
def parse_request():
    logging.debug("entering parse_request")
    if request.content_type == "application/json" and request.data is not None:
        json_dict = json.loads(request.data.decode("utf8"))
        password = json_dict['password']
        username = json_dict['username']
        uid = authenticate(username, password)
        if uid is not None:
            data = '{"auth": "' + uid + '"}'
            response = response_create(data, 200)
        else:
            data = "{'message': 'user unauthorized'}"
            response = response_create(data, 401)
    else:
        data = "{'message': 'json data expected'}"
        logging.error("Bad request received")
        response = response_create(data, 400)
    logging.debug("leaving parse_request")
    return response


@app.route('/', methods=['GET'])
def parse_request1():
    return jsonify(response="success")


# API that the camera hits to poll for request from server to send logs
@app.route('/camera/<camera_id>/polling', methods=['GET'])
def poll_for_log_request(camera_id):
    logging.debug("entering poll_for_log_request")
    entity = "user"
    if request.content_type == "application/json" and 'auth' in request.headers:
        entity = verify(request.headers.get('auth'))
    if entity == "user":
        data = "{'message': 'user unauthorized or malformed json or empty auth'}"
        logging.error("user unauthorized")
        response = response_create(data, 401)
        return response
    x = Helper.get_queue_1()
    while True:
        # wait until new user request comes for asking the event logs.
        if x.qsize() != 0:
            data = "{'message': 'request logs'}"
            logging.info("user requested logs of camera")
            response = response_create(data, 200)
            logging.debug("leaving poll_for_log_request")
            return response


# user hits this API (it does not require trusted Auth token) to fetch the logs from the camera.
@app.route('/logs', methods=['GET'])
def request_logs():
    logging.debug("entering request_logs")
    x = Helper.get_queue_1()
    # some dummy data. Could be user id for future reference for multiple user request.
    data = {
        "name": "external user"
    }
    x.put(data)
    y = Helper.get_queue()
    while True:
        # poll unless the second queue is filled with the data to be responded back to the user
        if y.qsize() != 0:
            logging.info("received logs on the queue to be forwarded to web client/user")
            data = json.loads(y.get())
            response = response_create(data, 200)
            logging.debug("leaving request_logs")
            return response


# Provide the server with the necessary logs as requested by the user.
@app.route('/camera/<camera_id>/logs', methods=['POST'])
def post_logs(camera_id):
    logging.debug("entering post_logs")
    auth = request.headers['auth']
    entity = "user"
    if request.content_type == "application/json" and auth:
        entity = verify(auth)
    if entity == "user":
        logging.error("user unauthorized")
        data = "{'message': 'user unauthorized or malformed json or empty auth'}"
        # unauthorized or malformed json request comes here. Error code handling to be done accordingly.
        response = response_create(data, 401)
        return response
    x = Helper.get_queue_1()
    # The camera was alerted using this queue to submit the logs.
    # As the logs are received we can dequeue the entry from the Queue
    x.get()
    # if we want to send empty log file to user/web client
    # if request.data is None:
    #     data = '{"events": []}'
    #     response = response_create(data, 202)
    data = request.data.decode("utf8")
    if data is not None:
        logging.info("received logs from the camera")
        y = Helper.get_queue()
        # put entire logs into the queue to be read by the controller that user had hit
        y.put(data)
        logging.debug("inserted logs into the queue")
        response = response_create(data, 202)
    else:
        data = "{'message': 'something went wrong while forwarding logs to the user. There were no events to show'}"
        logging.warning("most likely there are no events to show at this point or some Internal server Error")
        response = response_create(data, 500)
    logging.debug("leaving post_logs")
    return response


if __name__ == '__main__':
    logging.info("Flask app starting now")
    app.run(host='0.0.0.0', threaded=True)
