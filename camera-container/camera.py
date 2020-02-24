import os
import threading
import time
import requests
import json
import logging

logging.basicConfig(filename='camera.log', level=logging.DEBUG)
URL = "http://172.18.0.21:5000/"


# get the auth token for the camera for identity and authentication of certain private APIs
def get_auth():
    logging.debug("wait for server to come up.")
    time.sleep(10)
    headers = {
        "content-type": "application/json"
    }
    username_password_file = "username.txt"
    with open(username_password_file) as up:
        body = json.load(up)
    if body is None:
        # Depends on how to control such situation.
        return None
    url = URL + "session"
    body = str(body).replace("'", '"')
    response = requests.post(url, headers=headers, data=body)
    logging.info("received status code for %s is %s", url, str(response.status_code))
    response_str = response.content.decode("utf8")
    response_json = json.loads(str(json.loads(response_str)))
    return response_json['auth']


# read the logs file as json which is to be forwarded to the web client
def read_logs_as_json():
    event_array = {"events": []}
    log_file = 'to_logs_file.txt'
    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
        logging.info("reading the event log file to send to the server")
        with open(log_file, 'r') as content_file:
            event_count = 0
            while True:
                event_count += 1
                line = content_file.readline().replace("\n", "")
                if not line:
                    logging.debug("no more logs to read")
                    break
                logging.debug("read new line from event logs file")
                event_array["events"].append({"event " + str(event_count): line})
            event_str = str(event_array).replace("'", '"')
    else:
        logging.error("Event log file not found or is empty")
        return None
    return event_str


# send logs to the web client received from the camera
def send_logs(auth):
    for i in range(0, 3):
        url = URL + "camera/1/logs"
        logging.debug("Trying post  %s - %s time", url, str(i+1))
        headers = {
            "content-type": "application/json",
            "auth": auth
        }
        event_str = read_logs_as_json()
        if event_str is None:
            logging.warning("no data found in events log file. waiting for next 10 secs to have some data")
            time.sleep(10)
            # response = requests.post(url, headers=headers, data=None) # we can also empty logs to webclient.
            # mostly happens on startup before writing logs
        else:
            response = requests.post(url, headers=headers, data=event_str)
            logging.info("response from server for post %s is %s", url, str(response.status_code))
            if response.status_code == 202:
                break


# polling the server to receive request and then submit logs if server responds to the request
def poll_for_request():
    auth = get_auth()
    if auth is None:
        logging.error("Could not authenticate. System failure")
        exit(1)  # exit with error code 1 if there is an error in authentication
    while True:
        headers = {
            "content-type": "application/json",
            "auth": auth
        }
        url = URL + "camera/1/polling"
        try:
            response = requests.get(url, headers=headers, timeout=60)
            logging.info("get on %s gave %s status code", url, str(response.status_code))
            if response.status_code == 200:
                logging.info("server requested for event logs.")
                send_logs(auth)
        except requests.exceptions.RequestException as e:
            logging.warning(e)


# updates log file for now from the content of dummy log file. This dummy file will be replaced by actual data in
# real system
def update_log_file():
    count = 0
    with open("all_logs_file.txt", "r") as rf:
        while True:
            with open("to_logs_file.txt", "a") as wf:
                count += 1
                line = rf.readline()
                if not line:
                    break
                wf.write(line)
            logging.debug("sleeping for 10 secs")
            time.sleep(10)


# create two threads : one for writing to the log file one for polling the server
if __name__ == "__main__":
    logging.info("creating two threads to poll server and update log files")
    t1 = threading.Thread(target=poll_for_request)
    t2 = threading.Thread(target=update_log_file)
    logging.info("starting both the threads.")
    t1.start()
    t2.start()
