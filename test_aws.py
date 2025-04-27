import json
import subprocess
import threading
import time
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import os, sys
from dotenv import load_dotenv
import requests

from sub.scheduler import one_time_schedule, one_time_scheduler, periodic_scheduler, schedule_config
from libs.edit import deleteItem, file_changed_request, putItem  # type: ignore

load_dotenv()
res_file_path= os.environ.get('res_file_path')
schedules_file_path = os.environ.get('schedules_file_path')
rules_file_path = os.environ.get('rules_file_path')
rooms_file_path = os.environ.get('rooms_file_path')
devices_file_path = os.environ.get('devices_file_path')
notifications_file_path = os.environ.get('notifications_file_path')

HA_host = os.environ.get('HA_host')
hass_token = os.environ.get('hass_token')
matterhub_id = os.environ.get('matterhub_id')

# AWS IoT Core의 Thing 이름, 엔드포인트, 포트, 인증서 경로 등을 설정
thing_name = matterhub_id
host = "a2zr6a6gzb5fod-ats.iot.ap-northeast-2.amazonaws.com"
root_ca = "./cert/root-CA.crt"
private_key = "./cert/matterHub.private.key"
certificate = "./cert/matterHub.cert.pem"
port = 8883

# AWS IoT MQTT 클라이언트 초기화
mqtt_client = AWSIoTMQTTClient(thing_name)
mqtt_client.configureEndpoint(host, port)
mqtt_client.configureCredentials(root_ca, private_key, certificate)

# MQTT 클라이언트 구성 (타임아웃, 재연결 간격 등 설정)
mqtt_client.configureAutoReconnectBackoffTime(1, 32, 20)
mqtt_client.configureOfflinePublishQueueing(-1)  # 무제한 큐잉
mqtt_client.configureDrainingFrequency(2)  # 드레인 속도 (Hz)
mqtt_client.configureConnectDisconnectTimeout(10)  # 연결/해제 타임아웃
mqtt_client.configureMQTTOperationTimeout(10)  # MQTT 작업 타임아웃


def check_dynamic_endpoint(target_endpoint, endpoint, target_method, method): 
    url_var_list = []
    if(target_method!=method):
        return False
    
    target_endpoint_list = target_endpoint.split('/')
    endpoint_list = endpoint.split('/')

    if(len(target_endpoint_list) != len(endpoint_list)):
        return False
    
    for index in range(len(target_endpoint_list)):
        if(target_endpoint_list[index]=='_'):
            url_var_list.append(endpoint_list[index])
        else:
            if(target_endpoint_list[index]!=endpoint_list[index]):
                return False
    
    return url_var_list


def ota_callback(client, userdata, message):
    print(f"Received message: {message.payload.decode('utf-8')} from topic: {message.topic}")
    subprocess.run(['git', 'pull','origin','master'])
    try:
        print("프로그램을 재시작합니다...")
        time.sleep(10)  # 재시작 전 잠깐 대기 (옵션)
        command_with_sudo = f'echo matterhub | sudo -S reboot'
        subprocess.run(command_with_sudo, shell=True)
        return 'Success', 200
    except Exception as e:
        print(f"재시작 중 에러가 발생했습니다: {e}")
        return 'No update', 200
    return 'Invalid request', 400

# 메시지 콜백 함수
def message_callback(client, userdata, message):
    print(f"Received message: {message.payload.decode('utf-8')} from topic: {message.topic}")

def api_reqeust_callback(client, userdata, message) : 
    _message = json.loads(message.payload.decode('utf-8'))
    try : 
        endpoint = _message['endpoint']
        method = _message['method']
    except : 
        # endpoint, method가 없는 경우 예외처리
        pass

    if(endpoint=="/services"):
        print(f"Received message: {message.payload.decode('utf-8')} from topic: {message.topic}")
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(f"{HA_host}/api/services", headers=headers)
        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : response.json
        }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return

    if(endpoint=="/states" and method=="get"):
        print(f"Received message: {message.payload.decode('utf-8')} from topic: {message.topic}")
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(f"{HA_host}/api/states", headers=headers)
        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : json.loads(response.content)
        }
        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return

    check_res = check_dynamic_endpoint("/states/_",endpoint,"get",method)
    if(check_res):
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(f"{HA_host}/api/states/{check_res[0]}", headers=headers)
        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : json.loads(response.content)
        }
        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return

    check_res = check_dynamic_endpoint("/devices/_/command",endpoint,"post",method)
    if(check_res):
        headers = {"Authorization": f"Bearer {hass_token}"}
        domain = _message['payload']['domain']
        service = _message['payload']['service']

        res = {
            "entity_id":check_res[0]
        }
        response = requests.post(f"{HA_host}/api/services/{domain}/{service}", data=json.dumps(res), headers=headers)
        
        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : json.loads(response.content)
        }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return  
        
    check_res = check_dynamic_endpoint("/devices/_/status",endpoint,"get",method)
    if(check_res):
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(f"{HA_host}/api/states/{check_res[0]}", headers=headers)

        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : json.loads(response.content)
        }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return 
    

    check_res = check_dynamic_endpoint("/devices/_/services",endpoint,"get",method)
    if(check_res):
        target_entity = check_res[0]
        target_domain = target_entity.split('.')[0]
        
        url = f"{HA_host}/api/services"
        headers = {"Authorization": f"Bearer {hass_token}"}
        response = requests.get(url, headers=headers)
        all_domain = json.loads(response.content)
        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : json.loads(response.content)
        }

        switch_services = {}
        for d in all_domain:
            if(d['domain'] == target_domain):
                switch_services = d['services']
                break
        
        
        res = {
                "endpoint" : endpoint,
                "method" : method,
                "data" : switch_services
            }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return 

    if(endpoint=="/devices" and method in ["get","post","delete","put"]):
        try:
            with open(devices_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []  # 파일이 없으면 빈 리스트로 초기화
        
        if method == "post":
            new_data = _message['payload']
            data.append(new_data)
        if method == "delete":
            target_value =  _message['payload']['entity_id']
            data = deleteItem(data, "entity_id", target_value)
        if method == "put":
            target_value =  _message['payload']['entity_id']
            data = putItem(data, "entity_id", target_value, _message['payload'])
        if method == "get":
            pass

        # 업데이트된 데이터를 JSON 파일에 다시 저장5
        with open(devices_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)


        res = {
                "endpoint" : endpoint,
                "method" : method,
                "data" : data
            }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return 
    

    if(endpoint=="/schedules" and method in ["get","post","delete","put"]):
        try:
            with open(schedules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []  # 파일이 없으면 빈 리스트로 초기화
        
        if method == "post":
            new_data = _message['payload']
            data.append(new_data)
        if method == "delete":
            target_value =  _message['payload']['id']
            data = deleteItem(data, "id", target_value)
        if method == "put":
            target_value =  _message['payload']['id']
            data = putItem(data, "id", target_value, _message['payload'])
        if method == "get":
            pass

        # 업데이트된 데이터를 JSON 파일에 다시 저장5
        with open(schedules_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        if(method!="get"):
            schedule_config(one_time)
        res = {
                "endpoint" : endpoint,
                "method" : method,
                "data" : data
            }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return 
    
    if(endpoint=="/rules" and method=="get"):
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []  # 파일이 없으면 빈 리스트로 초기화\
        
        with open(rules_file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        res = {
            "endpoint" : endpoint,
            "method" : method,
            "data" : data
        }

        mqtt_client.publish(f"matterhub/{matterhub_id}/api/response", json.dumps(res), 0)
        return



    print(_message)

def create_certificates_callback(client, userdata, message):
    try:
        cert_data = json.loads(message.payload.decode('utf-8'))
        
        # 새 인증서 저장
        with open(certificate, "w") as f:
            f.write(cert_data["certificatePem"])
        with open(private_key, "w") as f:
            f.write(cert_data["privateKey"])
            
        print("새 인증서가 생성되었습니다.")
        return True
    except Exception as e:
        print(f"인증서 저장 중 오류 발생: {e}")
        return False

def create_new_certificates():
    try:
        # Claim 인증서로 임시 MQTT 클라이언트 생성
        claim_mqtt_client = AWSIoTMQTTClient("temp_" + thing_name)
        claim_mqtt_client.configureEndpoint(host, port)
        claim_mqtt_client.configureCredentials(root_ca, claim_private_key, claim_certificate)
        
        # 연결
        claim_mqtt_client.connect()
        
        # 인증서 응답을 받을 토픽 구독
        claim_mqtt_client.subscribe(
            f"$aws/certificates/{thing_name}/response",
            1,
            create_certificates_callback
        )
        
        # 인증서 생성 요청
        claim_mqtt_client.publish(
            f"$aws/certificates/{thing_name}/create",
            json.dumps({"thingName": thing_name}),
            1
        )
        
        # 응답 대기
        time.sleep(5)
        
        # 연결 해제
        claim_mqtt_client.disconnect()
        return True
        
    except Exception as e:
        print(f"인증서 생성 중 오류 발생: {e}")
        return False

def config():
    if not os.path.exists(res_file_path):
        os.makedirs(res_file_path)
        print(f"폴더 생성: {res_file_path}")

    # 인증서 파일 존재 여부 확인
    if not (os.path.exists(certificate) and os.path.exists(private_key)):
        print("인증서 파일이 없습니다. Claim 인증서로 새 인증서를 생성합니다.")
        if not create_new_certificates():
            print("인증서 생성 실패. 프로그램을 종료합니다.")
            sys.exit(1)

    file_list = [schedules_file_path, rules_file_path, rooms_file_path, devices_file_path, notifications_file_path]
    
    for f in file_list:
        if not os.path.exists(f):
            with open(f, 'w') as f:
                json.dump([], f)
            print(f"{f} 파일이 생성되었습니다.")


config()

one_time = one_time_schedule()
schedule_config(one_time)
p = threading.Thread(target=periodic_scheduler)
p.start()
o = threading.Thread(target=one_time_scheduler, args=[one_time])
o.start()

# MQTT 연결

while True:
    try:
        mqtt_client.connect()
        print("Reconnected to AWS IoT")
        break
    except Exception as e:
        print(f"Reconnection failed: {e}")
        time.sleep(5)

# 구독(subscribe)
mqtt_client.subscribe("sdk/test/python", 1, message_callback)
mqtt_client.subscribe(f"matterhub/{matterhub_id}/api/request", 1, api_reqeust_callback)
mqtt_client.subscribe(f"matterhub/ota", 1, ota_callback)

# 퍼블리시(publish) 테스트
def publish_message(topic, message):
    print(f"Publishing message: {message} to topic: {topic}")
    mqtt_client.publish(topic, message, 1)

# 메시지 퍼블리시
publish_message("sdk/test/python", "Hello, AWS IoT!")

# 10초 동안 메시지를 대기
while(1):
    time.sleep(1)

# 연결 해제
mqtt_client.disconnect()
