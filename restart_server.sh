#!/bin/bash

timestamp() {
    date +"%Y-%m-%dT%H:%M:%S"
}

# Stop the server
pkill -f main.py

# Move the old log file to the log directory
if [ -f nohup.out ]; then
    filename="log_$(timestamp)"
    mv nohup.out ServerLogs/$filename
fi
# Restart MySQL Server to prevent database errors
echo moxie100 | sudo -S service mysql restart

# Restart the server
nohup python -u main.py &
