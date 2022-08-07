# Pull Webots Docker image
ARG BASE_IMAGE=cyberbotics/webots:R2021b-ubuntu20.04
FROM ${BASE_IMAGE}

# added by Bahar
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys A4B469963BF863CC
RUN apt-get update && apt-get install -y --no-install-recommends apt-utils

RUN apt install build-essential

# Install required python libraries
RUN apt update && apt install --yes python3-pip && rm -rf /var/lib/apt/lists/
RUN pip3 install matplotlib
RUN pip3 install Pillow
RUN pip3 install numpy
RUN pip3 install scipy

# added by Bahar
# RUN sudo apt-key del 7fa2af80
# RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-keyring_1.0-1_all.deb
# RUN sudo dpkg -i cuda-keyring_1.0-1_all.deb

# Run script to launch the simulation
ENTRYPOINT ["bash","/usr/local/efs/demo/run_experiment.sh"]
