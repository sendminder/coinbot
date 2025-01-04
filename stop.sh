#!/bin/bash
pid=$(ps aux | grep "[p]ython3 main.py" | awk '{print $2}')
if [ -n "$pid" ]; then
    echo "Trading bot (PID: $pid) 종료 중..."
    kill $pid
    echo "종료되었습니다."
else
    echo "실행 중인 Trading bot을 찾을 수 없습니다."
fi
