import json
import boto3
import time
import uuid
import logging
from decimal import Decimal

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

iot = boto3.client('iot-data', region_name='ap-northeast-2')
dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
table = dynamodb.Table('matterhub-mqtt-responses')

def convert_decimals(obj):
    """Convert Decimal objects to regular Python types for JSON serialization"""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {key: convert_decimals(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    else:
        return obj

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")
        
        body = json.loads(event['body'])
        topic = body.get('topic', 'default/topic')
        message = body.get('message', {'msg': 'no message'})
        
        logger.info(f"Processing request - Topic: {topic}, Message: {message}")
        
        # 응답을 받을 topic 생성
        response_topic = f"{topic}/response"
        
        # 고유한 request_id 생성
        request_id = response_topic
        
        # message에 응답 topic 정보 추가
        if isinstance(message, str):
            message_with_response_topic = {
                'content': message,
                'response_topic': response_topic,
                'request_id': request_id
            }
        else:
            message_with_response_topic = {
                **message,
                'response_topic': response_topic,
                'request_id': request_id
            }
        
        logger.info(f"Publishing to topic: {topic}")
        logger.info(f"Message payload: {json.dumps(message_with_response_topic)}")
        
        # 메시지 발행
        try:
            response = iot.publish(
                topic=topic,
                qos=1,
                payload=json.dumps(message_with_response_topic)
            )
            logger.info(f"Publish response: {response}")
            
            # 발행 성공 확인
            if 'ResponseMetadata' in response and response['ResponseMetadata'].get('HTTPStatusCode') == 200:
                logger.info(f"Message published successfully")
                publish_success = True
            else:
                logger.error(f"Unexpected publish response: {response}")
                publish_success = False
                
        except Exception as publish_error:
            logger.error(f"Error publishing message: {str(publish_error)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error', 
                    'message': f'MQTT 발행 실패: {str(publish_error)}',
                    'topic': topic
                })
            }
        
        if not publish_success:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'message': '메시지 발행에 실패했습니다.',
                    'topic': topic,
                    'request_id': request_id
                })
            }
        
        # 응답 대기 (최대 30초)
        logger.info(f"Waiting for response on topic: {response_topic}")
        
        max_wait_time = 10
        wait_interval = 1
        start_time = time.time()
        response_message = None
        
        while time.time() - start_time < max_wait_time:
            try:
                # DynamoDB에서 응답 확인
                response_item = table.get_item(
                    Key={'response_id': response_topic}
                )
                
                if 'Item' in response_item:
                    response_data = response_item['Item']
                    response_message = convert_decimals(response_data)
                    logger.info(f"Response received: {response_message}")
                    
                    # 응답 데이터 정리
                    response_payload = {
                        'status': 'success',
                        'request_id': request_id,
                        'published_topic': topic,
                        'response_topic': response_topic,
                        'published_message': message_with_response_topic,
                        'response_message': response_message,
                        'response_timestamp': response_data.get('timestamp'),
                        'message': '응답을 성공적으로 받았습니다.'
                    }
                    
                    # DynamoDB에서 응답 데이터 삭제 (선택사항)
                    try:
                        table.delete_item(Key={'response_id': request_id})
                    except Exception as delete_error:
                        logger.warning(f"Failed to delete response from DynamoDB: {delete_error}")
                    
                    return {
                        'statusCode': 200,
                        'body': json.dumps(response_payload)
                    }
                
                # 응답이 없으면 잠시 대기
                time.sleep(wait_interval)
                
            except Exception as poll_error:
                logger.error(f"Error polling for response: {str(poll_error)}")
                logger.error(f"Response topic: {response_topic}")
                time.sleep(wait_interval)
        
        # 타임아웃 발생
        logger.warning(f"Timeout waiting for response on topic: {response_topic}")
        return {
            'statusCode': 408,  # Request Timeout
            'body': json.dumps({
                'status': 'timeout',
                'message': '응답을 받지 못했습니다. response_topic을 확인해주세요.',
                'request_id': request_id,
                'response_topic': response_topic,
                'published_topic': topic
            })
        }
        
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        }
