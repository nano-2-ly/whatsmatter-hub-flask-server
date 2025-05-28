#!bin/bash

mkdir matterhub
cd matterhub
git init
git remote add origin https://github.com/nano-2-ly/whatsmatter-hub-flask-server.git
git pull origin master
sudo apt install python3-pip
pip install -r requirements.txt --break-system-packages
sudo cp matterhub.service /etc/systemd/system

