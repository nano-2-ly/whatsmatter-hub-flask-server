import asyncio
import websockets
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()
hass_token = os.environ.get('hass_token')
HA_host = os.environ.get('HA_host')

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
            if(event['event']['data']['new_state']['entity_id'] == rule['trigger']['entity_id']):
                if(event['event']['data']['new_state']['state'] == rule['trigger']['state']):
                    service(rule['condition'], rule['action']['domain'], rule['action']['service'], rule['action']['entity_id'])

def service(condition, domain, service, entity):
    if (checkCondition(condition)):
        headers = {"Authorization": f"Bearer {hass_token}"}
        body = {"entity_id": entity}

        response = requests.post(f"{HA_host}/api/services/{domain}/{service}", data=json.dumps(body), headers=headers)
        print(response)
        print(response.content)

def checkCondition(condition):
    for c in condition:
        headers = {"Authorization": f"Bearer {hass_token}"}

        response = requests.get(f"{HA_host}/api/states/{c['entity_id']}", headers=headers)
        response = json.loads(response.content)

        if(c['option']==""):
            if (response['state'] == c['state']):
                pass
            else : 
                return False
        if(c['option']=="equal"):
            if (response['state'] == c['state']):
                pass
            else : 
                return False
    
    return True





async def subscribe(r):
    uri = f"ws://{HA_host.replace("http://","")}/api/websocket"
    async with websockets.connect(uri) as websocket:
        response = await websocket.recv()
        print(f"Received from server: {response}")

        await websocket.send(json.dumps(auth_body))
        response = await websocket.recv()
        print(f"Received from server: {response}")

        await websocket.send(json.dumps(subscribe_state_changed_body))
        response = await websocket.recv()
        print(f"Received from server: {response}")

        await websocket.send(json.dumps(subscribe_file_changed_body))
        response = await websocket.recv()
        print(f"Received from server: {response}")

        while(1):
            response = await websocket.recv()
            # print(f"Received from server: {response}")
            event = json.loads(response)
            if(event['event']['event_type']=="state_changed"):
                r.run_pending(event)
            if(event['event']['event_type']=="rules_file_changed"):
                r.file_reload()

if __name__ == "__main__":
    r = rule_engine()

    asyncio.run(subscribe(r))