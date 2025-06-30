#!/bin/bash

cd /home/hyodol/Desktop/matterhub
python3 sub/ruleEngine.py &
python3 sub/notifier.py &
python3 sub/localIp.py &
python3 app.py &
python3 mqtt.py &

wait
