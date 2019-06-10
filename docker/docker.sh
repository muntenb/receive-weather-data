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
	sensors:latest /bin/bash 
}

if [[ $# -ne 1 ]]; then
	echo "Usage: docker.sh (build|attach|run)"
	exit 1 
elif [[ $1 == "build" ]]; then
	build
elif [[ $1 == "attach" ]]; then
	attach
elif [[ $1 == "run" ]]; then
	run
else
	echo "Unknown argument: $1"
fi
