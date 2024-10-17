#!/bin/bash

cp matterhub /etc/init.d
cd /etc/init.d
chmod 775 matterhub
sudo update-rc.d matterhub defaults