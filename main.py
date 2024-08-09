from flask import Flask, request, jsonify
import requests
import schedule
import time
import json
import threading
from sub.scheduler import *

schedule_file_path = "resources/schedule.json"


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
    response = requests.get("http://192.168.1.195:8123/api/", headers=headers)
    return str(response.json())

@app.route('/local/api/states')
def states():
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJiY2E5MWY1OTJjZDg0ZmU0YTRiMWRjYTJiZWI5ZWQ4MSIsImlhdCI6MTcyMjUwMTI3NSwiZXhwIjoyMDM3ODYxMjc1fQ.TpTXTBFyuOwQY5mOVuLy4MTUGfCkZ3ZVFh7xHnprW5I"}
    response = requests.get("http://192.168.1.195:8123/api/states", headers=headers)
    return str(response.json())

@app.route('/local/api/rules', methods=["POST"])
def rules():
    if request.method == "POST":
        new_data = request.json
        # 파일에서 기존 데이터 읽기
        try:
            with open(schedule_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []  # 파일이 없으면 빈 리스트로 초기화

        # 새로운 데이터를 기존 데이터에 추가
        data.append(new_data)

        # 업데이트된 데이터를 JSON 파일에 다시 저장5
        with open(schedule_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        schedule_config(one_time)
        return str(new_data)
    

if __name__ == '__main__':
    app.run(debug=True)