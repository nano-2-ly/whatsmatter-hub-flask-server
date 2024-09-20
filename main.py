from flask import Flask, request, jsonify
import requests
import schedule
import time
import json
import threading
from sub.scheduler import *
from sub.ruleEngine import *
from utils import *
from dotenv import load_dotenv
import os
import subprocess

from utils.edit import deleteItem, file_changed_request, putItem 

load_dotenv()
res_file_path= os.environ.get('res_file_path')
schedules_file_path = os.environ.get('schedules_file_path')
rules_file_path = os.environ.get('rules_file_path')
rooms_file_path = os.environ.get('rooms_file_path')
devices_file_path = os.environ.get('devices_file_path')
notifications_file_path = os.environ.get('notifications_file_path')

HA_host = os.environ.get('HA_host')
hass_token = os.environ.get('hass_token')


def config():

    if not os.path.exists(res_file_path):
        os.makedirs(res_file_path)
        print(f"폴더 생성: {res_file_path}")


    file_list = [schedules_file_path, rules_file_path, rooms_file_path, devices_file_path, notifications_file_path]
    
    for f in file_list:
        if not os.path.exists(f):
            with open(f, 'w') as f:
                json.dump([], f)

            print(f"{f} 파일이 생성되었습니다.")


app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        # GitHub에서 보내는 이벤트가 맞는지 확인 (옵션)
        data = request.json
        if data['ref'] == 'refs/heads/master':  # main 브랜치가 업데이트된 경우
            # git pull로 코드 업데이트
            subprocess.run(['git', 'pull'])
            # Flask 서버 재시작 (필요한 경우)
            subprocess.run(['sudo', 'systemctl', 'restart', 'your-flask-service'])
            return 'Success', 200
        return 'No update', 200
    return 'Invalid request', 400

@app.route('/local/api', methods=["POST","DELETE", "PUT", "GET"])
def home():
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(f"{HA_host}/api/", headers=headers)
    
    return str(response.json())

@app.route('/local/api/services')
def services():
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(f"{HA_host}/api/services", headers=headers)
    return jsonify(response.json())

@app.route('/local/api/states')
def states():
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(f"{HA_host}/api/states", headers=headers)
    return jsonify(response.json())

@app.route('/local/api/states/<entity_id>')
def statesEntityId(entity_id):
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(f"{HA_host}/api/states/{entity_id}", headers=headers)
    return jsonify(response.json())

@app.route('/local/api/devices/<entity_id>/command', methods=["POST"])
def device_command(entity_id):
    headers = {"Authorization": f"Bearer {hass_token}"}
    body = {
        "entity_id": entity_id
        }
    _r = {**request.json}
    _r.pop('domain')
    _r.pop('service')
    merged_dict = {**body, **_r}
    print(merged_dict)
    response = requests.post(f"{HA_host}/api/services/{request.json['domain']}/{request.json['service']}", data=json.dumps(merged_dict), headers=headers)
    return jsonify(response.json()) 

@app.route('/local/api/devices/<entity_id>/status', methods=["GET"])
def device_status(entity_id):
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(f"{HA_host}/api/states/{entity_id}", headers=headers)
    return jsonify(response.json()) 

@app.route('/local/api/devices/<entity_id>/services', methods=["GET"])
def device_services(entity_id):
    target_entity = entity_id
    target_domain = target_entity.split('.')[0]

    url = f"{HA_host}/api/services"
    headers = {"Authorization": f"Bearer {hass_token}"}
    response = requests.get(url, headers=headers)
    all_domain = json.loads(response.content)

    for d in all_domain:
        if(d['domain'] == target_domain):
            switch_services = d['services']
            return jsonify(switch_services) 
    return jsonify({}) 


@app.route('/local/api/devices', methods=["POST","DELETE", "PUT", "GET"])
def devices():
    try:
        with open(devices_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화
    
    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        target_value =  request.json['entity']
        data = deleteItem(data, "entity", target_value)
    if request.method == "PUT":
        target_value =  request.json['entity']
        data = putItem(data, "entity", target_value, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(devices_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    schedule_config(one_time)
    return jsonify(data)



@app.route('/local/api/schedules', methods=["POST","DELETE", "PUT", "GET"])
def schdules():
    # 파일에서 기존 데이터 읽기
    try:
        with open(schedules_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화
    
    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        target_value =  request.json['id']
        data = deleteItem(data, "id", target_value)
    if request.method == "PUT":
        target_value =  request.json['id']
        data = putItem(data, "id", target_value, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(schedules_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    if(request.method!="GET"):
        schedule_config(one_time)
    return jsonify(data)

@app.route('/local/api/schedules/<schedule_id>', methods=["POST","DELETE", "PUT", "GET"])
def schdules_id(schedule_id):
    # 파일에서 기존 데이터 읽기
    try:
        with open(schedules_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화

    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        data = deleteItem(data, "id", schedule_id)
    if request.method == "PUT":
        data = putItem(data, "id", schedule_id, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(schedules_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    if(request.method!="GET"):
        schedule_config(one_time)

    return jsonify(data)

@app.route('/local/api/rules', methods=["POST","DELETE", "PUT", "GET"])
def rules():
    
    try:
        with open(rules_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화

    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        target_value =  request.json['id']
        data = deleteItem(data, "id", target_value)
    if request.method == "PUT":
        target_value =  request.json['id']
        data = putItem(data, "id", target_value, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(rules_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    if(request.method!="GET"):
        file_changed_request("rules_file_changed")
    return jsonify(data)

@app.route('/local/api/rooms', methods=["POST","DELETE", "PUT", "GET"])
def rooms():
    try:
        with open(rooms_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화

    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        target_value =  request.json['id']
        data = deleteItem(data, "id", target_value)
    if request.method == "PUT":
        target_value =  request.json['id']
        data = putItem(data, "id", target_value, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(rooms_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    schedule_config(one_time)
    return jsonify(data)
    
@app.route('/local/api/notifications', methods=["POST","DELETE", "PUT", "GET"])
def notifications():
    try:
        with open(notifications_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
    except FileNotFoundError:
        data = []  # 파일이 없으면 빈 리스트로 초기화

    if request.method == "POST":
        new_data = request.json
        data.append(new_data)
    if request.method == "DELETE":
        target_value =  request.json['id']
        data = deleteItem(data, "id", target_value)
    if request.method == "PUT":
        target_value =  request.json['id']
        data = putItem(data, "id", target_value, request.json)
    if request.method == "GET":
        pass

    # 업데이트된 데이터를 JSON 파일에 다시 저장5
    with open(notifications_file_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

    if(request.method!="GET"):
        res= file_changed_request("notifications_file_changed")
        print(res.content)
    return jsonify(data)




    
config()

one_time = one_time_schedule()
schedule_config(one_time)
p = threading.Thread(target=periodic_scheduler)
p.start()
o = threading.Thread(target=one_time_scheduler, args=[one_time])
o.start()

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True,port=8000)
