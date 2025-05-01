#!/bin/bash

echo "[*] Membuat direktori /root/telegram-bot"
sudo mkdir -p /root/telegram-bot
sudo chmod 777 /root /root/telegram-bot

echo "[*] Memindahkan file..."
cd /workspace/code
sudo cp stx.py run_bot.sh commands.sh /root/telegram-bot

echo "[*] Pindah ke folder bot..."
cd /root/telegram-bot || exit

echo "[*] Install Telebot & dependencies..."
sudo rm -rf /usr/lib/python3/dist-packages/blinker* 
sudo rm -rf /usr/local/lib/python3.*/dist-packages/blinker* 
sudo rm -rf /usr/lib/python3.*/dist-packages/blinker* 
sudo pip3 install --upgrade setuptools pip 
sudo python3 -m pip install --upgrade pip
sudo pip3 install --no-cache-dir flask python-telegram-bot==20.8
sudo pip3 install --no-cache-dir telegram psutil datetime requests
sudo pip3 install python-telegram-bot --upgrade

echo "[*] Menginstall supervisord jika belum ada..."
if ! command -v supervisord &> /dev/null; then
    sudo apt update && sudo apt install -y supervisor
fi

echo "[*] Membuat konfigurasi supervisord untuk bot..."
sudo tee /etc/supervisor/conf.d/telegram-bot.conf > /dev/null <<EOF
[program:telegram-bot]
directory=/root/telegram-bot
command=/usr/bin/python3 /root/telegram-bot/stx.py
autostart=true
autorestart=true
stderr_logfile=/var/log/telegram-bot.err.log
stdout_logfile=/var/log/telegram-bot.out.log
EOF

echo "[*] Mengaktifkan supervisord di systemd..."
sudo systemctl enable supervisor
sudo systemctl start supervisor

echo "[*] Reload supervisord dan mulai bot..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start telegram-bot

echo "[✓] Bot berhasil diinstal dan dijalankan melalui supervisord!"
echo "[✓] Akan otomatis jalan saat reboot."
