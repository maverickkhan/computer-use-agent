#!/bin/bash
echo "[DEBUG] tint2_startup.sh: DISPLAY is '$DISPLAY'"
which tint2 || echo "[DEBUG] tint2 not found in PATH"
xdpyinfo || echo "[DEBUG] xdpyinfo failed"
echo "starting tint2 on display $DISPLAY ..."

# Wait for Xvfb to be ready
timeout=10
while ! xdpyinfo >/dev/null 2>&1; do
    if [ $timeout -le 0 ]; then
        echo "[DEBUG] Xvfb is not ready, exiting"
        exit 1
    fi
    sleep 1
    ((timeout--))
done

# Start tint2 and capture its stderr
tint2 -c $HOME/.config/tint2/tint2rc 2>/tmp/tint2_stderr.log &

# Wait for tint2 window properties to appear
timeout=30
while [ $timeout -gt 0 ]; do
    if xdotool search --class "tint2" >/dev/null 2>&1; then
        break
    fi
    sleep 1
    ((timeout--))
done

if [ $timeout -eq 0 ]; then
    echo "[DEBUG] tint2 stderr output:" >&2
    cat /tmp/tint2_stderr.log >&2
    exit 1
fi

rm /tmp/tint2_stderr.log
