#!/bin/bash

set -e

# Setup pyenv
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"
eval "$(pyenv init -)"

# Start virtual X desktop, panel, window manager, VNC, etc
./start_all.sh
./novnc_startup.sh

# Start FastAPI backend (from /home/computeruse/app)
cd $HOME/app
export DISPLAY=:$DISPLAY_NUM
uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/fastapi.log 2>&1 &

# Start nginx (for reverse proxy/static serving)
sudo nginx

echo "✨ Everything started! Open http://localhost:8080"
tail -f /dev/null
