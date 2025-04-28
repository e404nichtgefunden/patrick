#!/bin/bash

echo "[*] Membuat direktori /root/telegram-bot"
sudo chmod 777 /root
sudo mkdir -p /root/telegram-bot

echo "[*] Memindahkan file..."
cd /workspace/patrick
sudo cp stx.py telegram-bot.service run_bot.sh commands.sh /root/telegram-bot

echo "[*] Pindah ke folder bot..."
cd /root/telegram-bot || exit

echo "[*] Install Telebot..."
sudo rm -rf /usr/lib/python3/dist-packages/blinker* 
sudo rm -rf /usr/local/lib/python3.*/dist-packages/blinker* 
sudo rm -rf /usr/lib/python3.*/dist-packages/blinker* 
pip3 install --upgrade setuptools pip 
sudo pip3 install --no-cache-dir flask python-telegram-bot==20.8
sudo pip3 install --no-cache-dir telegram psutil datetime
sudo python3 -m pip install --upgrade pip
sudo pip3 install python-telegram-bot --upgrade
sudo chmod 777 /etc
sudo chmod 777 /etc/systemd
sudo chmod 777 /etc/systemd/system

echo "[*] Menyalin systemd service..."
sudo cp telegram-bot.service /etc/systemd/system

echo "[*] Menyesuaikan path di service file..."
sudo sed -i "s|/root/stx.py|/root/telegram-bot|g" /etc/systemd/system/telegram-bot.service
sudo sed -i "s|/root/stx.py|/root/telegram-bot/stx.py|g" /etc/systemd/system/telegram-bot.service

echo "[*] Reload systemd..."
sudo systemctl daemon-reload

echo "[*] Enable dan start bot..."
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot

echo "[✓] Bot berhasil diinstall, systemd aktif!"

sudo nohup /usr/bin/python3 /root/telegram-bot/stx.py > /workspace/nohup.stx 2>&1
cd /
sudo chmod +x root && sudo chmod +x /root/telegram-bot && sudo chmod +x /root/telegram-bot/run_bot.sh && sudo nohup /usr/bin/bash ./root/telegram-bot/run_bot.sh > /workspace/stxxx.out 2>&1 


