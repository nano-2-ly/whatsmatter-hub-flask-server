import json
import os
import threading
import time
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
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

# 전역 변수로 선언
mqtt_connection = None

class AWSIoTClient:
    def __init__(self):
        self.cert_path = "certificates/"
        self.claim_cert = "whatsmatter_nipa_claim_cert.cert.pem"
        self.claim_key = "whatsmatter_nipa_claim_cert.private.key"
        self.endpoint = "a206qwcndl23az-ats.iot.ap-northeast-2.amazonaws.com"
        self.client_id = "whatsmatter-nipa-claim-thing"

        # Ensure certificates directory exists
        if not os.path.exists(self.cert_path):
            try:
                os.makedirs(self.cert_path)
                print(f"Created certificates directory: {self.cert_path}")
            except Exception as e:
                print(f"Failed to create certificates directory: {e}")

    def check_certificate(self):
        """발급된 인증서 확인"""
        cert_file = os.path.join(self.cert_path, "device.pem.crt")
        key_file = os.path.join(self.cert_path, "private.pem.key")
        
        if os.path.exists(cert_file) and os.path.exists(key_file):
            return True, cert_file, key_file
        return False, None, None

    def provision_device(self):
        """Claim 인증서를 사용하여 새 인증서 발급 및 사물 등록"""
        try:
            # Claim 인증서로 MQTT 클라이언트 생성
            event_loop_group = io.EventLoopGroup(1)
            host_resolver = io.DefaultHostResolver(event_loop_group)
            client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

            print(f"Claim 인증서 경로: {os.path.join(self.cert_path, self.claim_cert)}")
            print(f"Claim 키 경로: {os.path.join(self.cert_path, self.claim_key)}")
            
            try:
                mqtt_connection = mqtt_connection_builder.mtls_from_path(
                    endpoint=self.endpoint,
                    cert_filepath=os.path.join(self.cert_path, self.claim_cert),
                    pri_key_filepath=os.path.join(self.cert_path, self.claim_key),
                    client_bootstrap=client_bootstrap,
                    client_id=self.client_id,
                    keep_alive_secs=30
                )
            except Exception as e:
                print(f"MQTT 클라이언트 생성 실패: {e}")
                return False
            
            print("MQTT 연결 시도 중...")
            try:
                connect_future = mqtt_connection.connect()
                connect_future.result(timeout=10)
                print("MQTT 연결 성공")
            except Exception as e:
                print(f"MQTT 연결 실패: {e}")
                return False
            
            # 인증서 발급 요청
            provision_topic = "$aws/certificates/create/json"
            response_topic = "$aws/certificates/create/json/accepted"
            
            # 응답 대기를 위한 플래그
            received_response = False
            new_cert_data = None
            
            def on_message_received(topic, payload, **kwargs):
                nonlocal received_response, new_cert_data
                print(f"인증서 응답 수신: {payload.decode()}")
                new_cert_data = json.loads(payload.decode())
                received_response = True
            
            try:
                subscribe_future, _ = mqtt_connection.subscribe(
                    topic=response_topic,
                    qos=mqtt.QoS.AT_LEAST_ONCE,
                    callback=on_message_received
                )
                subscribe_future.result(timeout=10)
            except Exception as e:
                print(f"토픽 구독 실패: {e}")
                mqtt_connection.disconnect()
                return False
            
            print("인증서 발급 요청 중...")
            try:
                publish_future, _ = mqtt_connection.publish(
                    topic=provision_topic,
                    payload=json.dumps({}),
                    qos=mqtt.QoS.AT_LEAST_ONCE
                )
                publish_future.result(timeout=10)
            except Exception as e:
                print(f"인증서 요청 발행 실패: {e}")
                mqtt_connection.disconnect()
                return False
            
            # 응답 대기
            timeout = time.time() + 10
            while not received_response and time.time() < timeout:
                time.sleep(0.1)
            
            if not received_response:
                print("인증서 발급 응답 시간 초과")
                mqtt_connection.disconnect()
                return False
                
            if new_cert_data:
                # 새 인증서 저장
                try:
                    with open(os.path.join(self.cert_path, "device.pem.crt"), "w") as f:
                        f.write(new_cert_data["certificatePem"])
                    with open(os.path.join(self.cert_path, "private.pem.key"), "w") as f:
                        f.write(new_cert_data["privateKey"])
                    
                    print("인증서 파일 저장 완료")
                except Exception as e:
                    print(f"인증서 파일 저장 실패: {e}")
                    mqtt_connection.disconnect()
                    return False
                
                # 인증서 발급 후 사물 등록 진행
                success = self.register_thing(
                    mqtt_connection, 
                    new_cert_data["certificateId"],
                    new_cert_data["certificateOwnershipToken"]
                )
                mqtt_connection.disconnect()
                return success
                
            mqtt_connection.disconnect()
            return False
        except Exception as e:
            print(f"인증서 발급 실패: {e}")
            return False

    def register_thing(self, mqtt_connection, certificate_id, cert_ownership_token):
        """템플릿을 사용하여 사물 등록"""
        try:
            template_topic = "$aws/provisioning-templates/whatsmatter-nipa-template/provision/json"
            response_topic = "$aws/provisioning-templates/whatsmatter-nipa-template/provision/json/accepted"
            
            received_response = False
            registration_data = None
            
            def on_registration_response(topic, payload, **kwargs):
                nonlocal received_response, registration_data
                registration_data = json.loads(payload.decode())
                received_response = True
            
            # 등록 응답 구독
            subscribe_future, _ = mqtt_connection.subscribe(
                topic=response_topic,
                qos=mqtt.QoS.AT_LEAST_ONCE,
                callback=on_registration_response
            )
            subscribe_future.result(timeout=10)
            
            # 등록 요청 전송
            registration_request = {
                "Parameters": {
                    "SerialNumber": f"SN-{int(time.time())}"  # 실제 디바이스 이름으로 변경 필요
                },
                "certificateOwnershipToken": cert_ownership_token,
                "certificateId": certificate_id
            }
            
            print("사물 등록 요청 중...")
            publish_future, _ = mqtt_connection.publish(
                topic=template_topic,
                payload=json.dumps(registration_request),
                qos=mqtt.QoS.AT_LEAST_ONCE
            )
            publish_future.result(timeout=10)
            
            # 응답 대기
            timeout = time.time() + 10
            while not received_response and time.time() < timeout:
                time.sleep(0.1)
            
            if registration_data:
                print("사물 등록 성공:", registration_data)
                # Update matterhub_id in .env with the registered thingName
                with open('.env', 'r') as f:
                    env_content = f.read()
                env_content = env_content.replace(f'matterhub_id = "{os.environ.get("matterhub_id")}"', f'matterhub_id = "{registration_data["thingName"]}"')
                with open('.env', 'w') as f:
                    f.write(env_content)
                os.environ['matterhub_id'] = registration_data['thingName']
                global matterhub_id
                matterhub_id = registration_data['thingName']
                return True
            
            print("사물 등록 실패: 응답 없음")
            return False
            
        except Exception as e:
            print(f"사물 등록 실패: {e}")
            return False

    def connect_mqtt(self):
        """인증서를 사용하여 MQTT 연결"""
        has_cert, cert_file, key_file = self.check_certificate()
        
        if not has_cert:
            success = self.provision_device()
            if not success:
                raise Exception("인증서 발급 실패")
            has_cert, cert_file, key_file = self.check_certificate()
            
        # 새로운 인증서로 연결할 때는 client_id를 다르게 설정
        self.client_id = matterhub_id  # 고유한 client_id 생성
        
        event_loop_group = io.EventLoopGroup(1)
        host_resolver = io.DefaultHostResolver(event_loop_group)
        client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
        
        mqtt_connection = mqtt_connection_builder.mtls_from_path(
            endpoint=self.endpoint,
            cert_filepath=cert_file,
            pri_key_filepath=key_file,
            client_bootstrap=client_bootstrap,
            client_id=self.client_id,
            keep_alive_secs=30  # keep_alive 설정 추가
        )
        
        print("새 인증서로 MQTT 연결 시도 중...")
        connect_future = mqtt_connection.connect()
        connect_future.result()
        print("새 인증서로 MQTT 연결 성공")
        
        return mqtt_connection

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

def handle_ha_request(endpoint, method, request_func):
    """Home Assistant API 요청을 처리하고 응답을 반환하는 공통 함수"""
    try:
        response = request_func()
        res = {
            "endpoint": endpoint,
            "method": method,
            "status": "success",
            "data": response.json()
        }
    except Exception as e:
        print(f"Error: {e}")
        res = {
            "endpoint": endpoint,
            "method": method,
            "status": "error",
            "data": []
        }
    print(f"Response: {res}")
    
    global_mqtt_connection.publish(
        topic=f"matterhub/{matterhub_id}/api/response",
        payload=json.dumps(res),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )
    return

def send_api_documentation(topic, error_message=None, response_topic=None):
    """API 사용법 설명을 전송하는 함수"""
    api_docs = {
        "status": "error",
        "error": error_message or "Invalid request format",
        "documentation": {
            "message_format": {
                "endpoint": "API 엔드포인트 (예: '/devices', '/states')",
                "method": "HTTP 메소드 (예: 'get', 'post', 'put', 'delete')",
                "payload": "요청 데이터 (선택적, method에 따라 필요)"
            },
            "supported_endpoints": [
                {
                    "endpoint": "/services",
                    "methods": ["get"],
                    "description": "사용 가능한 서비스 목록 조회"
                },
                {
                    "endpoint": "/states",
                    "methods": ["get"],
                    "description": "모든 상태 정보 조회"
                },
                {
                    "endpoint": "/states/{entity_id}",
                    "methods": ["get"],
                    "description": "특정 엔티티의 상태 조회"
                },
                {
                    "endpoint": "/devices/{entity_id}/command",
                    "methods": ["post"],
                    "payload": {
                        "domain": "서비스 도메인 (예: 'light', 'switch')",
                        "service": "서비스 명령 (예: 'turn_on', 'turn_off')"
                    },
                    "description": "디바이스에 명령 전송"
                },
                {
                    "endpoint": "/devices/{entity_id}/status",
                    "methods": ["get"],
                    "description": "디바이스 상태 조회"
                },
                {
                    "endpoint": "/devices/{entity_id}/services",
                    "methods": ["get"],
                    "description": "디바이스에서 사용 가능한 서비스 조회"
                },
                {
                    "endpoint": "/devices",
                    "methods": ["get", "post", "put", "delete"],
                    "description": "디바이스 목록 관리"
                },
                {
                    "endpoint": "/schedules",
                    "methods": ["get", "post", "put", "delete"],
                    "description": "스케줄 관리"
                },
                {
                    "endpoint": "/rules",
                    "methods": ["get", "post", "put", "delete"],
                    "description": "자동화 규칙 관리"
                }
            ],
            "examples": [
                {
                    "description": "조명 켜기 예제",
                    "message": {
                        "endpoint": "/devices/light.living_room/command",
                        "method": "post",
                        "payload": {
                            "domain": "light",
                            "service": "turn_on"
                        }
                    }
                },
                {
                    "description": "디바이스 상태 확인 예제",
                    "message": {
                        "endpoint": "/devices/switch.kitchen/status",
                        "method": "get"
                    }
                }
            ]
        }
    }
    
    # 기본 응답 토픽 설정
    if response_topic is None:
        response_topic = f"matterhub/{matterhub_id}/api/response"
    
    print(f"Sending API documentation due to invalid request: {error_message}")
    global_mqtt_connection.publish(
        topic=response_topic,
        payload=json.dumps(api_docs),
        qos=mqtt.QoS.AT_LEAST_ONCE
    )

def mqtt_callback(topic, payload, **kwargs):
    try:
        _message = json.loads(payload.decode('utf-8'))
    except json.JSONDecodeError:
        send_api_documentation(topic, "Invalid JSON format in message payload")
        return

    try:
        endpoint = _message['endpoint']
        method = _message['method']
        
        # 기본 유효성 검사
        if not isinstance(endpoint, str) or not endpoint.startswith('/'):
            send_api_documentation(topic, "Invalid endpoint format. Must be a string starting with '/'")
            return
            
        if not isinstance(method, str) or method.lower() not in ['get', 'post', 'put', 'delete']:
            send_api_documentation(topic, "Invalid method. Must be one of: 'get', 'post', 'put', 'delete'")
            return
            
        # 메소드 소문자로 정규화
        method = method.lower()
        
    except KeyError:
        send_api_documentation(topic, "Missing required fields: 'endpoint' and 'method' are required")
        return

    headers = {"Authorization": f"Bearer {hass_token}"}

    # Payload 유효성 검사 함수
    def validate_payload_for_method():
        # POST, PUT 메소드는 payload가 필요함
        if method in ['post', 'put'] and ('payload' not in _message or not _message['payload']):
            send_api_documentation(topic, f"Missing 'payload' field required for '{method}' requests")
            return False
        return True

    # endpoint별 처리 전 payload 검증
    if not validate_payload_for_method():
        return

    # 여기서부터 기존 코드와 동일하게 진행
    if endpoint == "/services":
        print(f"Received message: {payload} from topic: {topic} endpoint: {endpoint} method: {method}")
        handle_ha_request(
            endpoint,
            method,
            lambda: requests.get(f"{HA_host}/api/services", headers=headers)
        )
        return

    if endpoint == "/states" and method == "get":
        print(f"Received message: {payload} from topic: {topic} endpoint: {endpoint} method: {method}")
        handle_ha_request(
            endpoint,
            method,
            lambda: requests.get(f"{HA_host}/api/states", headers=headers)
        )
        return

    check_res = check_dynamic_endpoint("/states/_",endpoint,"get",method)
    if(check_res):
        print(f"Received message: {payload} from topic: {topic} endpoint: {endpoint} method: {method}")
        handle_ha_request(
            endpoint,
            method,
            lambda: requests.get(f"{HA_host}/api/states/{check_res[0]}", headers=headers)
        )
        return

    check_res = check_dynamic_endpoint("/devices/_/command",endpoint,"post",method)
    if(check_res):
        try:
            domain = _message['payload']['domain']
            service = _message['payload']['service']
            print(f"Received message: {payload} from topic: {topic} endpoint: {endpoint} method: {method}")
            res = {
                "entity_id": check_res[0]
            }
            handle_ha_request(
                endpoint,
                method,
                lambda: requests.post(f"{HA_host}/api/services/{domain}/{service}", 
                                    data=json.dumps(res), 
                                    headers=headers)
            )
        except KeyError as e:
            missing_field = str(e).strip("'")
            send_api_documentation(topic, f"Missing required field in payload: {missing_field} for device command")
        except Exception as e:
            send_api_documentation(topic, f"Error processing device command: {str(e)}")
        return

    check_res = check_dynamic_endpoint("/devices/_/status",endpoint,"get",method)
    if(check_res):
        handle_ha_request(
            endpoint,
            method,
            lambda: requests.get(f"{HA_host}/api/states/{check_res[0]}", headers=headers)
        )
        return

    check_res = check_dynamic_endpoint("/devices/_/services",endpoint,"get",method)
    if(check_res):
        target_entity = check_res[0]
        target_domain = target_entity.split('.')[0]
        
        def get_domain_services():
            response = requests.get(f"{HA_host}/api/services", headers=headers)
            all_domain = response.json()
            for d in all_domain:
                if(d['domain'] == target_domain):
                    return {"json": lambda: d['services']}
            return {"json": lambda: {}}
            
        handle_ha_request(
            endpoint,
            method,
            get_domain_services
        )
        return

    if(endpoint=="/devices" and method in ["get","post","delete","put"]):
        try:
            with open(devices_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []
        
        try:
            if method == "post":
                new_data = _message['payload']
                data.append(new_data)
            if method == "delete":
                target_value = _message['payload']['entity_id']
                data = deleteItem(data, "entity_id", target_value)
            if method == "put":
                target_value = _message['payload']['entity_id']
                data = putItem(data, "entity_id", target_value, _message['payload'])

            with open(devices_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            def mock_request():
                return type('Response', (), {'json': lambda: data})()

            handle_ha_request(endpoint, method, mock_request)
        except KeyError as e:
            missing_field = str(e).strip("'")
            error_message = f"Missing required field: {missing_field}"
            if method == "delete" or method == "put":
                error_message += " ('entity_id' is required for delete/put operations)"
            send_api_documentation(topic, error_message)
        except Exception as e:
            send_api_documentation(topic, f"Error processing {endpoint} request: {str(e)}")
        return

    if(endpoint=="/schedules" and method in ["get","post","delete","put"]):
        try:
            with open(schedules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []
        
        try:
            if method == "post":
                new_data = _message['payload']
                data.append(new_data)
            if method == "delete":
                target_value = _message['payload']['id']
                data = deleteItem(data, "id", target_value)
            if method == "put":
                target_value = _message['payload']['id']
                data = putItem(data, "id", target_value, _message['payload'])

            with open(schedules_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            if(method != "get"):
                schedule_config(one_time)

            def mock_request():
                return type('Response', (), {'json': lambda: data})()

            handle_ha_request(endpoint, method, mock_request)
        except KeyError as e:
            missing_field = str(e).strip("'")
            error_message = f"Missing required field: {missing_field}"
            if method == "delete" or method == "put":
                error_message += " ('id' is required for delete/put operations)"
            send_api_documentation(topic, error_message)
        except Exception as e:
            send_api_documentation(topic, f"Error processing {endpoint} request: {str(e)}")
        return

    if(endpoint=="/rules" and method in ["get","post","delete","put"]):
        try:
            with open(rules_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            data = []
        
        try:
            if method == "post":
                new_data = _message['payload']
                data.append(new_data)
            if method == "delete":
                target_value = _message['payload']['id']
                data = deleteItem(data, "id", target_value)
            if method == "put":
                target_value = _message['payload']['id']
                data = putItem(data, "id", target_value, _message['payload'])

            with open(rules_file_path, 'w', encoding='utf-8') as file:
                json.dump(data, file, indent=4, ensure_ascii=False)

            def mock_request():
                return type('Response', (), {'json': lambda: data})()

            handle_ha_request(endpoint, method, mock_request)
        except KeyError as e:
            missing_field = str(e).strip("'")
            error_message = f"Missing required field: {missing_field}"
            if method == "delete" or method == "put":
                error_message += " ('id' is required for delete/put operations)"
            send_api_documentation(topic, error_message)
        except Exception as e:
            send_api_documentation(topic, f"Error processing {endpoint} request: {str(e)}")
        return

    # If we reach here, it means no valid endpoint handler was found
    send_api_documentation(topic, f"Unknown or unsupported endpoint: {endpoint}")

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

# 사용 예시
if __name__ == "__main__":
    config()

    one_time = one_time_schedule()
    schedule_config(one_time)
    p = threading.Thread(target=periodic_scheduler)
    p.start()
    o = threading.Thread(target=one_time_scheduler, args=[one_time])
    o.start()

    aws_client = AWSIoTClient()
    global_mqtt_connection = aws_client.connect_mqtt()  # global 키워드 제거
    print("MQTT 연결 성공")
    
    # hello 토픽 구독
    subscribe_future, packet_id = global_mqtt_connection.subscribe(
        topic=f"matterhub/{matterhub_id}/api",
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=mqtt_callback
    )
    subscribe_result = subscribe_future.result()
    print(f"matterhub/{matterhub_id}/api 토픽 구독 완료")

    # 테스트용 데이터 publish
    test_data = {
        "message": "테스트 메시지",
        "timestamp": time.time()
    }
    

    
    try:
        # 무한 루프로 메시지 수신 대기
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("프로그램 종료")
        global_mqtt_connection.disconnect()
