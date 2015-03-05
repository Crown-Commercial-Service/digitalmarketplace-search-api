#!/bin/bash
source ./venv/bin/activate 2>/dev/null && echo "Virtual environment activated."

# Use default environment vars for localhost if not already set
export DM_SEARCH_API_AUTH_TOKENS=${DM_SEARCH_API_AUTH_TOKENS:=myToken}
export DM_ELASTICSEARCH_URL=${DM_ELASTICSEARCH_URL:=http://localhost:9200}

echo "Environment variables in use:"
env | grep DM_

python application.py runserver
