#!/bin/bash
# local connection to the 868MHz antenna
DEVICE="/dev/bus/usb/001/003"

function build {
docker build -t sensors .
}

function attach {
docker run -it --privileged --rm --name sensors-devel \
	--device=$DEVICE \
	--link influxdb_cont:influxdb_cont \
	--volume /home/pi/github/receive-weather-data/docker/homeClimate:/app/homeClimate \
	--volume /etc/localtime:/etc/localtime:ro \
	--entrypoint /bin/bash \
	sensors:latest 
}

function run {
docker run -d -t --privileged --restart=always \
	--name sensors-read \
	--link influxdb_cont:influxdb_cont \
	--device=$DEVICE \
	--volume /etc/localtime:/etc/localtime:ro \
	sensors:latest
}

function stop {
docker container stop sensors-read
docker container rm sensors-read
}

function rm {
docker container rm sensors-read
}

if [[ $# -ne 1 ]]; then
	echo "Usage: docker.sh (build|attach|run|stop|rm)"
	exit 1 
elif [[ $1 == "build" ]]; then
	build
elif [[ $1 == "attach" ]]; then
	attach
elif [[ $1 == "run" ]]; then
	run
elif [[ $1 == "stop" ]]; then
	stop
elif [[ $1 == "rm" ]]; then
	rm
else
	echo "Unknown argument: $1"
fi
