import requests
from dotenv import load_dotenv
import os
HA_host = os.environ.get('HA_host')
hass_token = os.environ.get('hass_token')

load_dotenv()

def deleteItem(data, target_key, target_value):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   

    return filtered_dict_list


def putItem(data, target_key, target_value, new_item):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   
    filtered_dict_list.append(new_item)
    return filtered_dict_list


def file_changed_request(event_type):
    # rules.json 또는 notifications.json의 내용이 변경되면 
    # ruleEngine.py와 notifier.py에서 변경된 사실을 인지해야합니다.
    # 이를 위한 함수입니다.
    headers = {"Authorization": f"Bearer {hass_token}"}

    response = requests.post(f"{HA_host}/api/events/{event_type}", headers=headers)
    return response