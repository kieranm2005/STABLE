#!/bin/bash
# Make scripts executable
chmod +x /home/pi/your-repo/deploy/start_app.sh

# Link the service file to systemd
sudo ln -sf /home/pi/your-repo/deploy/my_project.service /etc/systemd/system/my_project.service

# Refresh systemd and enable
sudo systemctl daemon-reload
sudo systemctl enable my_project.service
echo "Deployment complete! Run 'sudo systemctl start my_project' to begin."