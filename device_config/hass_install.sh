#!bin/bash

sudo apt update
sudo apt install apparmor jq wget curl udisks2 libglib2.0-bin network-manager dbus systemd-journal-remote -y
curl -fsSL get.docker.com | sh
wget https://github.com/home-assistant/os-agent/releases/download/1.6.0/os-agent_1.6.0_linux_aarch64.deb
sudo dpkg -i os-agent_1.6.0_linux_aarch64.deb
wget https://github.com/home-assistant/supervised-installer/releases/latest/download/homeassistant-supervised.deb
sudo dpkg -i homeassistant-supervised.deb
sudo BYPASS_OS_CHECK=true dpkg -i homeassistant-supervised.deb
sudo apt --fix-broken install
sudo apt --fix-broken install
