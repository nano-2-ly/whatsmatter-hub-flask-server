import requests
from dotenv import load_dotenv
import os
HA_host = os.environ.get('HA_host')
hass_token = os.environ.get('hass_token')

load_dotenv()

expected_rule_structure = {
    "id": str,
    "alias": int,
    "trigger": {
      "state": str,
      "entity_id": str,
      "option": str
    },
    "condition": [
      {
        "state": str,
        "entity_id": str,
        "option": str
      }
    ],
    "action": {
      "domain": str,
      "service": str,
      "entity_id": str
    }
}

expected_notification_structure = {
    "id": str,
    "alias": str,
    "trigger": {
      "state": str,
      "entity_id": str,
      "option": str
    },
    "condition": [
      {
        "state": str,
        "entity_id": str,
        "option": str
      }
    ],
    "action": {
      "url": str
    }
}

expected_schedule_structure = {
    "id": str,
    "alias": str,
    "schedule": {
      "type": str,
      "period": object
    },
    "condition": [
      {
        "entity": str,
        "state": str,
        "option": str
      }
    ],
    "action": {
      "domain": str,
      "service": str,
      "entity": str
    }
}


def deleteItem(data, target_key, target_value):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   

    return filtered_dict_list


def putItem(data, target_key, target_value, new_item):
    filtered_dict_list = [item for item in data if item.get(target_key) != target_value]   
    filtered_dict_list.append(new_item)
    return filtered_dict_list

def paylad_validation(data, type):
    if(type == 'rule'): 
        pass
    elif(type == 'notification'): 
        pass
    elif(type == 'schedule'): 
        pass
    else :
        return {'result' : 'failed', "message" : "유효한 type이 아닙니다."}
    return False

def file_changed_request(event_type):
    # rules.json 또는 notifications.json의 내용이 변경되면 
    # ruleEngine.py와 notifier.py에서 변경된 사실을 인지해야합니다.
    # 이를 위한 함수입니다.
    headers = {"Authorization": f"Bearer {hass_token}"}

    response = requests.post(f"{HA_host}/api/events/{event_type}", headers=headers)
    return response