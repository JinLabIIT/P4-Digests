#!/bin/bash

# Paths to the controller scripts
S1_CONTROLLER="./controllers/s1_controller.py"
S2_CONTROLLER="./controllers/s2_controller.py"
S3_CONTROLLER="./controllers/s3_controller.py"

# Function to start a controller in the background
start_controller() {
    local controller=$1
    echo "Starting $controller..."
    python "$controller" &
    echo "$controller started with PID $!"
}

# Function to stop all controllers
stop_controllers() {
    echo "Stopping all controllers..."
    pkill -f s1_controller.py
    pkill -f s2_controller.py
    pkill -f s3_controller.py
    echo "All controllers stopped."
    exit 0
}

# Trap Ctrl+C (SIGINT) to stop controllers gracefully
trap stop_controllers SIGINT

# Start all controllers
start_controller "$S1_CONTROLLER"
start_controller "$S2_CONTROLLER"
start_controller "$S3_CONTROLLER"

# Wait indefinitely to keep the script running
echo "All controllers started. Press Ctrl+C to stop."
while true; do
    sleep 1
done