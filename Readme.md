<<<<<<< HEAD
In a client server environment. Lets assume there is a camera which is generating logs every 10 secs.
The logs are written to logs file : to_logs_file.txt on the camera client which has no open ports.
The server has only one open port and only one user facing api GET: /logs/. 

One booting up both the docker containers, client camera will poll the server to ask for logs.
As soon as the user requests for the logs to the server on the same port the server replies back to the client camera requesting for the logs.
The client camera then sends the logs using a private API and hence the user receives the logs from the server that belongs to camera client.

Steps to run this:-

=======
>>>>>>> 910aad400e4cd8a14feb6618c0058aea4e0d6acc
To start the system run:-
	cmd: docker-compose up
at the location where docker-compose.yml is residing.

To get the docker machine ip:-
	cmd: docker-machine ip
at the location where docker-compose.yml is residing.
Default: 192.168.99.100

The dummy curl requests from webclient to fetch logs are:-
	cmd: curl -X GET http://192.168.99.100:5000/logs -H 'content-type: application/json'
Note that the flask app is running on default port=5000
