This is the first round interview submission by Harsh Shah(iamharsh@umd.edu).

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