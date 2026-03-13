#!/bin/bash
set -e

uvicorn main:app --host 127.0.0.1 --port 8000 &

sleep 2

nginx -g "daemon off;"
