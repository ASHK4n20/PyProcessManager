#!/bin/bash

# Install the Python package
pip3 install -e .

# Create log files
sudo touch /var/log/pypm.log /var/log/pypm.error.log
sudo chmod 644 /var/log/pypm.log /var/log/pypm.error.log

# Copy service file to systemd
sudo cp pypm.service /etc/systemd/system/

# Reload systemd daemon
sudo systemctl daemon-reload

# Enable and start the service
sudo systemctl enable pypm.service
sudo systemctl start pypm.service

echo "PyPM has been installed! You can now use 'pypm' command anywhere."
echo "To check service status: sudo systemctl status pypm"
echo "To view logs: tail -f /var/log/pypm.log"
