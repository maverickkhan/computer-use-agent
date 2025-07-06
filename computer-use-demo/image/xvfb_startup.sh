#!/bin/bash
set -e

echo "[DEBUG] In xvfb_startup.sh: DISPLAY='$DISPLAY', DISPLAY_NUM='$DISPLAY_NUM', WIDTH='$WIDTH', HEIGHT='$HEIGHT'"
which Xvfb || echo "[DEBUG] Xvfb not found"
Xvfb -help || echo "[DEBUG] Could not run Xvfb -help"
env | grep DISPLAY

DPI=96
RES_AND_DEPTH=${WIDTH}x${HEIGHT}x24

# Function to check if Xvfb is already running
check_xvfb_running() {
    if [ -e /tmp/.X${DISPLAY_NUM}-lock ]; then
        return 0  # Xvfb is already running
    else
        return 1  # Xvfb is not running
    fi
}

# Function to check if Xvfb is ready
wait_for_xvfb() {
    local timeout=10
    local start_time=$(date +%s)
    while ! xdpyinfo >/dev/null 2>&1; do
        if [ $(($(date +%s) - start_time)) -gt $timeout ]; then
            echo "[DEBUG] Xvfb failed to start within $timeout seconds" >&2
            return 1
        fi
        sleep 0.1
    done
    return 0
}

# Check if Xvfb is already running
if check_xvfb_running; then
    echo "[DEBUG] Xvfb is already running on display ${DISPLAY}"
    exit 0
fi

# Start Xvfb
Xvfb $DISPLAY -ac -screen 0 $RES_AND_DEPTH -nolisten tcp -nolisten unix -fbdir /tmp &

XVFB_PID=$!

# Wait for Xvfb to start
if wait_for_xvfb; then
    echo "[DEBUG] Xvfb started successfully on display ${DISPLAY}"
    echo "[DEBUG] Xvfb PID: $XVFB_PID"
else
    echo "[DEBUG] Xvfb failed to start"
    kill $XVFB_PID
    exit 1
fi
