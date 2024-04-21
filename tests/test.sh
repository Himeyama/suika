#!/bin/bash

# 10回ループ
while true; do
    top -1 -b -n 1 -w 163 | grep -E "^%Cpu" | head -n 2 | nc localhost 8080
    # top -1 -b -n 1 -w 79 | grep -E "^%Cpu" | nc localhost 8080
    sleep 1  # 1秒待つ
done