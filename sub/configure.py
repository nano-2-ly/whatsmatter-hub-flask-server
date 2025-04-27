import json




device_file_path = "resources/devices.json"
room_file_path = "resources/roos.json"

def change_entity_alias(entity_id, new_alias):
    with open(device_file_path, 'r', encoding='utf-8') as file:
        device_list = json.load(file)

    for d in device_list:
        if(d['entity_id'] == entity_id):
            d['alias'] = new_alias

    with open(device_file_path, 'w', encoding='utf-8') as file:
        json.dump(device_list, file, indent=4, ensure_ascii=False)
    return d

def change_room_alias(room_id, new_alias):
    with open(room_file_path, 'r', encoding='utf-8') as file:
        room_list = json.load(file)

    for r in room_list:
        if(r['room_id'] == room_id):
            r['alias'] = new_alias

    with open(room_file_path, 'w', encoding='utf-8') as file:
        json.dump(room_list, file, indent=4, ensure_ascii=False)

    return r