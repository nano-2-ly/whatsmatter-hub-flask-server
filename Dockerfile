FROM python:3.9-slim

WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y git \
    && pip install --upgrade pip \
    && pip install awscrt python-dotenv requests paho-mqtt schedule \
    && pip install git+https://github.com/awslabs/aws-iot-device-sdk-python-v2.git

# 인증서 폴더 생성 및 복사
RUN mkdir -p /app/certificates
COPY certificates/ /app/certificates/

# 리소스 폴더 생성 및 복사
RUN mkdir -p /app/resources
COPY resources/ /app/resources/

# sub, libs 폴더 복사
COPY sub/ /app/sub/
COPY libs/ /app/libs/

# 소스 및 환경파일 복사
COPY mqtt.py /app/
COPY .env /app/

# 실행 권한 부여
RUN chmod +x /app/mqtt.py

# 애플리케이션 실행
CMD ["python", "/app/mqtt.py"]
