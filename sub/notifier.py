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
    "event_type": "notifications_file_changed"
}

def get_notifications():
    with open('resources/notifications.json', 'r', encoding='utf-8') as file:
        data = json.load(file)

        return data
    return [] 

class notifier() : 
    def __init__(self):
        self.notifications_list = get_notifications()

    def file_reload(self):
        self.notifications_list = get_notifications()

    def add_noti(self, r):
        self.notifications_list.append(r)

    def run_pending(self, event):
        for noti in self.notifications_list:
            if(event['event']['event_type']=="state_changed"):
                if(event['event']['data']['new_state']['entity_id'] == noti['trigger']['entity_id']):
                    if(event['event']['data']['new_state']['state'] == noti['trigger']['state']):
                        notify_to_url(noti['condition'], noti['action']['url'], event)

def notify_to_url(condition, url, payload):
    if (checkCondition(condition)):
        headers = {"Authorization": f"Bearer {hass_token}"}
        body = payload
        try : 
            response = requests.post(url, data=json.dumps(body), headers=headers)
            print(response.content)
        except : 
            print(f"notify url({url})이 잘못되었거나, 서버가 반응이 없습니다.")
        

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
            if(event['event']['event_type']=="notifications_file_changed"):
                print(f"Received from server: {response}")
                r.file_reload()

if __name__ == "__main__":
    r = notifier()

    asyncio.run(subscribe(r))