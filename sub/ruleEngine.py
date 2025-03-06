import asyncio
import websockets
import json
import requests
import os, time
from dotenv import load_dotenv

load_dotenv()
hass_token = os.environ.get('hass_token')
HA_host = os.environ.get('HA_host')

# 환경 변수 확인
if not HA_host:
    print("❌ HA_host 값이 없습니다. 환경 변수를 확인하세요.")
    exit(1)

if not hass_token:
    print("❌ HA 토큰이 없습니다. 환경 변수를 확인하세요.")
    exit(1)

auth_body = {
    "type": "auth",
    "access_token": hass_token
}

subscribe_state_changed_body = {
    "id": 18,
    "type": "subscribe_events",
    "event_type": "state_changed"
}

subscribe_file_changed_body = {
    "id": 19,
    "type": "subscribe_events",
    "event_type": "rules_file_changed"
}

def get_rules():
    with open('resources/rules.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
        return data
    return [] 

class rule_engine() : 
    def __init__(self):
        self.rules_list = get_rules()

    def file_reload(self):
        self.rules_list = get_rules()

    def add_rule(self, r):
        self.rules_list.append(r)

    def run_pending(self, event):
        for rule in self.rules_list:
            if(not rule['activate']):
                continue

            if(event['event']['data']['new_state']['entity_id'] == rule['trigger']['entity_id']):

                try:
                    _option = rule['trigger']['option']
                except KeyError:
                    _option = "equal"

                current_state = float(event['event']['data']['new_state']['state'])
                target_state = float(rule['trigger']['state'])

                if(_option == "equal" and current_state == target_state) or \
                   (_option == "greaterThan" and current_state > target_state) or \
                   (_option == "greaterThanOrEquals" and current_state >= target_state) or \
                   (_option == "lessThan" and current_state < target_state) or \
                   (_option == "lessThanOrEquals" and current_state <= target_state):
                    executeActions(rule)
                return

def executeActions(rule):
    if isinstance(rule['action'], dict):
        service(rule['condition'], rule['action']['domain'], rule['action']['service'], rule['action']['entity_id'])
    if isinstance(rule['action'], list):
        for r in rule['action']:
            service(rule['condition'], r['domain'], r['service'], r['entity_id'])

def service(condition, domain, service, entity):
    if checkCondition(condition):
        headers = {"Authorization": f"Bearer {hass_token}"}
        body = {"entity_id": entity}
        response = requests.post(f"{HA_host}/api/services/{domain}/{service}", json=body, headers=headers)
        print(response.status_code, response.text)

def checkCondition(condition):
    if not condition:
        return True

    for c in condition:
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(f"{HA_host}/api/states/{c['entity_id']}", headers=headers)

        if response.status_code != 200:
            print(f"❌ API 요청 실패! 상태 코드: {response.status_code}")
            print("응답 내용:", response.text)
            return False

        try:
            response_json = response.json()
        except json.JSONDecodeError:
            print("❌ JSON 디코딩 오류 발생! 응답 내용:", response.text)
            return False

        current_state = response_json['state']
        target_state = c['state']
        if c['option'] in ["", "equal"] and current_state == target_state:
            return True
        elif c['option'] == "greaterThan" and float(current_state) > float(target_state):
            return True
        elif c['option'] == "greaterThanOrEquals" and float(current_state) >= float(target_state):
            return True
        elif c['option'] == "lessThan" and float(current_state) < float(target_state):
            return True
        elif c['option'] == "lessThanOrEquals" and float(current_state) <= float(target_state):
            return True

    return False

async def subscribe(r):
    uri = f"ws://{HA_host.replace('http://','')}/api/websocket"
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                await websocket.send(json.dumps(auth_body))
                await websocket.send(json.dumps(subscribe_state_changed_body))
                await websocket.send(json.dumps(subscribe_file_changed_body))

                while True:
                    response = await websocket.recv()
                    event = json.loads(response)
                    if event['event']['event_type'] == "state_changed":
                        r.run_pending(event)
                    if event['event']['event_type'] == "rules_file_changed":
                        r.file_reload()
        except Exception as e:
            print(f"❌ WebSocket 연결 실패! 오류: {e}")
            time.sleep(5)

if __name__ == "__main__":
    r = rule_engine()
    asyncio.run(subscribe(r))

