#!/bin/bash

while true
do
    echo "Starting bot..."
    sudo nohup /usr/bin/python3 /root/telegram-bot/stx.py > /root/bot.log 2>&1
    echo "Bot crashed. Restarting in 5 seconds..."
    sleep 5
done
