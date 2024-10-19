#!/bin/bash

cp matterhub /etc/init.d
cd /etc/init.d
chmod 775 matterhub.sh
sudo update-rc.d matterhub defaults