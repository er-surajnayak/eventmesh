#!/bin/bash

# GCP Always Free - EventMesh Backend Auto-Deploy Script
# Target: Ubuntu 22.04 on e2-micro

# 1. Update and install core dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git nginx sqlite3

# 2. Memory optimization for e2-micro (1GB RAM)
# Add 2GB swap space to prevent memory crashes during scraping
if [ ! -f /swapfile ]; then
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

# 3. Setup Project
cd ~
git clone https://github.com/surajnayak/eventmesh.git || cd eventmesh
cd eventmesh/backend

# 4. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn uvicorn mangum

# 5. Initialize Database
export PYTHONPATH=$PYTHONPATH:.
python create_db.py

# 6. Create the Systemd Service
sudo bash -c "cat > /etc/systemd/system/eventmesh.service << EOF
[Unit]
Description=EventMesh Backend on GCP
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$(pwd)
Environment='PATH=$(pwd)/venv/bin'
Environment='PYTHONPATH=$(pwd)'
Environment='DEBUG=false'
Environment='DATABASE_URL=sqlite:///./eventmesh.db'
ExecStart=$(pwd)/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
EOF"

# 7. Start and Enable
sudo systemctl daemon-reload
sudo systemctl start eventmesh
sudo systemctl enable eventmesh

# 8. Firewall (Local to VM)
sudo ufw allow 8000

echo "------------------------------------------------"
echo "✅ GCP Backend is ready!"
echo "📍 IP: $(curl -s ifconfig.me)"
echo "📍 Port: 8000"
echo "------------------------------------------------"
