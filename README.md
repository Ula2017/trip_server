# Trip server

### Authors
Joanna Chyży, Ula Soboń

### Disclaimer
This repository contains source code for the server for trips chat application. 

### Configuring and running server locally
You need to have Python 3.x with pip installed.

```bash
$ git clone https://github.com/Ula2017/trip_server.git
$ cd trip_server
$ pip install --upgrade pip
$ pip install -r requirements.txt
$ python server.py
```

### Configuring and running server from image
You need need to have [Docker](https://www.docker.com/products/docker-desktop "Docker 's Homepage") installed.


##### Build your own image
Go to trip_server folder and run
```bash
$ docker build -t sobou/trip-image:latest .
```
The docker image *sobou/trip-image* was created. You can also pull image from docker-hub instead of creating your own.

##### Pull image from docker-hub
```bash
$ docker pull sobou/trip-image:latest
```

##### Create and run container
Create container
```bash
$ docker create --name trip-server -it -p 5000:5000 sobou/trip-image
```
To start or stop your container use
```bash
$ docker start trip-server
$ docker stop trip-server
```