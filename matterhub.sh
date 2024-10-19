#!bin/bash

cd /home/matterhub/Desktop/matterhub
python3 sub/ruleEngine.py &
python3 sub/notifier.py &
python3 app.py &
python3 aws.py &

wait