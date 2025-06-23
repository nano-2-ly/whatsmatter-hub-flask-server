import json
import boto3
import time
import logging

# 로깅 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb', region_name='ap-northeast-2')
table = dynamodb.Table('mqtt-responses')

def lambda_handler(event, context):
    """
    MQTT 응답을 받아서 DynamoDB에 저장하는 Lambda 함수
    AWS IoT Core Rule에서 호출됨
    """
    try:
        logger.info(f"Received MQTT event: {json.dumps(event)}")
        
        # MQTT 메시지에서 데이터 추출
        topic = event.get('topic', '')
        payload = event.get('payload', '{}')
        
        # payload가 문자열인 경우 JSON으로 파싱
        if isinstance(payload, str):
            try:
                payload_data = json.loads(payload)
            except json.JSONDecodeError:
                payload_data = {'raw_payload': payload}
        else:
            payload_data = payload
        
        # request_id 추출
        request_id = payload_data.get('request_id')
        
        if not request_id:
            logger.warning("No request_id found in payload")
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No request_id in payload'})
            }
        
        # DynamoDB에 응답 저장
        response_item = {
            'request_id': request_id,
            'topic': topic,
            'payload': payload_data,
            'timestamp': int(time.time()),
            'ttl': int(time.time()) + 3600  # 1시간 후 만료
        }
        
        try:
            table.put_item(Item=response_item)
            logger.info(f"Response stored in DynamoDB for request_id: {request_id}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'status': 'success',
                    'message': 'Response stored successfully',
                    'request_id': request_id
                })
            }
            
        except Exception as db_error:
            logger.error(f"Error storing response in DynamoDB: {str(db_error)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'status': 'error',
                    'message': f'Database error: {str(db_error)}'
                })
            }
            
    except Exception as e:
        logger.error(f"Lambda execution error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'status': 'error', 'message': str(e)})
        } 