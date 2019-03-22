FROM raspbian/stretch
LABEL maintainer="muntenb"

# install what is required to compile tfrec
RUN apt-get update && apt-get install -y \
	libcurl4-openssl-dev \
	libssl-dev \
	python3-picamera \
	python3-pip \
	git \
	curl \
	librtlsdr-dev \
	make \
	g++ \
	pkg-config \
    && rm -rf /var/lib/apt/lists/*

# python3 interface to influxdb
RUN pip3 install influxdb

# install tfrec
WORKDIR /app
RUN git clone https://github.com/baycom/tfrec.git \
	&& cd tfrec \
	&& make -f Makefile.arm \
	&& cp -v tfrec /usr/bin/tfrec

# copy the python app to process the data
COPY homeClimate /app/homeClimate
WORKDIR /app/homeClimate
ENTRYPOINT ["/usr/bin/python3", "homeClimate.py"]  

