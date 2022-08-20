#!/bin/bash
#OS=xUbuntu_22.04
OS=xUbuntu_20.04
#OS=Debian_11
CRIO_VERSION=1.24
SUB_VERSION=1.24.1

sudo apt -y update 
sudo apt -y upgrade
sudo apt install -y gpg # install gpg if it is not installed

echo "deb https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/ /"|sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable.list
echo "deb http://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable:/cri-o:/${CRIO_VERSION}:/${SUB_VERSION}/$OS/ /"|sudo tee /etc/apt/sources.list.d/devel:kubic:libcontainers:stable:cri-o:$CRIO_VERSION.list
curl -L https:///download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable:/cri-o:/${CRIO_VERSION}:/${SUB_VERSION}/$OS/Release.key | sudo apt-key add -
curl -L https://download.opensuse.org/repositories/devel:/kubic:/libcontainers:/stable/$OS/Release.key | sudo apt-key add -
sudo apt -y update
sudo apt -y upgrade
sudo apt install -y cri-o cri-o-runc podman cri-tools lldpd


