#!/bin/bash
# Make scripts executable
chmod +x /home/pi/STABLE/deploy/start_app.sh

# Link the service file to systemd
sudo ln -sf /home/pi/STABLE/deploy/start_app_service.service /etc/systemd/system/start_app_service.service

# Refresh systemd and enable
sudo systemctl daemon-reload
sudo systemctl enable start_app_service.service
echo "Deployment complete! Run 'sudo systemctl start start_app_service' to begin."