#!/bin/bash

echo "=== Upbit Auto Trading Bot 설치 시작 ==="

# Python 버전 체크
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    echo "Error: Python $required_version 이상이 필요합니다. (현재 버전: $python_version)"
    exit 1
fi

# 가상환경 생성
echo "가상환경 생성 중..."
python3 -m venv venv

# 가상환경 활성화
source venv/bin/activate

# 의존성 설치
echo "필요한 패키지 설치 중..."
pip install --upgrade pip
pip install -r requirements.txt

# 설정 파일 생성
echo "설정 파일 생성 중..."
if [ ! -f .env ]; then
    echo "UPBIT_ACCESS_KEY=" > .env
    echo "UPBIT_SECRET_KEY=" >> .env
    echo ".env 파일이 생성되었습니다. API 키를 설정해주세요."
fi

if [ ! -f src/config/config.yaml ]; then
    cp src/config/config.yaml.example src/config/config.yaml
    echo "config.yaml 파일이 생성되었습니다. 설정을 수정해주세요."
fi

# 로그 디렉토리 생성
echo "로그 디렉토리 생성 중..."
mkdir -p logs

echo """
=== 설치 완료! ===

다음 단계를 진행해주세요:
1. .env 파일에 API 키를 설정
2. src/config/config.yaml 파일에서 거래 설정 수정
3. 실행: python main.py

주의: 반드시 소액으로 테스트 후 사용하세요!
""" 