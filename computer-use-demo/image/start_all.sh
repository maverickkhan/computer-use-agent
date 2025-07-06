#!/bin/bash
set -e

echo "[DEBUG] start_all.sh: DISPLAY_NUM='$DISPLAY_NUM', DISPLAY='$DISPLAY', WIDTH='$WIDTH', HEIGHT='$HEIGHT'"
env | grep DISPLAY

: "${DISPLAY_NUM:=1}"
export DISPLAY=:${DISPLAY_NUM}

./xvfb_startup.sh
sleep 5  # Give Xvfb time to fully initialize

./tint2_startup.sh
./mutter_startup.sh
./x11vnc_startup.sh
