#!/bin/bash

# Oracle Cloud - EventMesh Backend Auto-Deploy Script
# Target: Ubuntu 22.04+

# 1. Update system and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git nginx sqlite3

# 2. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 3. Install Requirements
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn mangum

# 4. Initialize Database
export PYTHONPATH=$PYTHONPATH:.
python create_db.py

# 5. Create Systemd Service to keep it alive 24/7
sudo bash -c 'cat > /etc/systemd/system/eventmesh.service << EOF
[Unit]
Description=Gunicorn instance to serve EventMesh Backend
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
Environment="PYTHONPATH=$(pwd)"
Environment="DEBUG=false"
Environment="EVENTBRITE_API_KEY=YOUR_KEY_HERE"
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOF'

# 6. Start Service
sudo systemctl daemon-reload
sudo systemctl start eventmesh
sudo systemctl enable eventmesh

# 7. Open Firewall Port 8000 (standard on Oracle Linux/Ubuntu)
sudo ufw allow 8000
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 8000 -j ACCEPT
sudo netfilter-persistent save

echo "------------------------------------------------"
echo "✅ EventMesh Backend is now live on Port 8000!"
echo "📍 Your background scraper is running 24/7."
echo "------------------------------------------------"
