#!/bin/bash
# UptimeRobot Monitor Setup
# Requires: UPTIMEROBOT_API_KEY env var

API_KEY=$UPTIMEROBOT_API_KEY
BACKEND_URL="https://your-backend.onrender.com/api/v1/health"

curl -X POST "https://api.uptimerobot.com/v2/newMonitor" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "api_key=$API_KEY" \
  -d "format=json" \
  -d "type=1" \
  -d "url=$BACKEND_URL" \
  -d "friendly_name=Receipt Journal Health" \
  -d "interval=840"  # 14 minutes in seconds
