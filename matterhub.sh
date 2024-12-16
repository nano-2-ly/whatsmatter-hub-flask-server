#!bin/bash

cd /home/matterhub/Desktop/matterhub
python3 sub/ruleEngine.py &
python3 sub/notifier.py &
python3 app.py &
python3 aws.py &
ngrok start --all &

sleep 1m
echo "whatsmatter1234" | sudo-S iw reg set KR
sleep 1m
echo "whatsmatter1234" | sudo-S iw reg set KR
sleep 1m
echo "whatsmatter1234" | sudo-S iw reg set KR
sleep 1m
echo "whatsmatter1234" | sudo-S iw reg set KR
sleep 1m
echo "whatsmatter1234" | sudo-S iw reg set KR

wait
