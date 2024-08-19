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

from utils.edit import deleteItem, putItem 

load_dotenv()
schedules_file_path = os.environ.get('schedules_file_path')
rules_file_path = os.environ.get('rules_file_path')
rooms_file_path = os.environ.get('rooms_file_path')
devices_file_path = os.environ.get('devices_file_path')

HA_host = os.environ.get('HA_host')

one_time = one_time_schedule()
schedule_config(one_time)
p = threading.Thread(target=periodic_scheduler)
p.start()
o = threading.Thread(target=one_time_scheduler, args=[one_time])
o.start()



app = Flask(__name__)



@app.route('/local/api')
def home():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get(f"{HA_host}/api/", headers=headers)
    
    return jsonify(response.json())

@app.route('/local/api/states')
def states():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get(f"{HA_host}/api/states", headers=headers)
    return jsonify(response.json())

@app.route('/local/api/states/<entity_id>')
def statesEntityId(entity_id):
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get(f"{HA_host}/api/states/{entity_id}", headers=headers)
    return jsonify(response.json())

@app.route('/local/api/device/<entity_id>/command', methods=["POST"])
def device_command(entity_id):
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    body = {
        "entity_id": entity_id
        }
    response = requests.post(f"{HA_host}/api/services/{request.json['domain']}/{request.json['service']}", data=json.dumps(body), headers=headers)
    return jsonify(response.json()) 

@app.route('/local/api/device/<entity_id>/status', methods=["GET"])
def device_status(entity_id):
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get(f"{HA_host}/api/states/{entity_id}", headers=headers)
    return jsonify(response.json()) 

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

@app.route('/local/api/devices/<entity_id>/status', methods=["GET"])
def status(entity_id):
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get(f"{HA_host}/api/states/{entity_id}", headers=headers)
    return jsonify(response.json()) 


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

    schedule_config(one_time)
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
    

if __name__ == '__main__':
    app.run('0.0.0.0',debug=True,port=8000)
    