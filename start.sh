#!/bin/sh
# start.sh

# This script checks for an environment variable called 'PROCESS_TYPE'
# to decide which command to run.

if [ "$PROCESS_TYPE" = "web" ] ; then
  # If PROCESS_TYPE is "web", start the Uvicorn server
  uvicorn main:app --host 0.0.0.0 --port 8000
elif [ "$PROCESS_TYPE" = "worker" ] ; then
  # If PROCESS_TYPE is "worker", start the Celery worker
  celery -A celery_app.celery worker --loglevel=info --pool=solo
else
  echo "Error: PROCESS_TYPE environment variable not set."
  exit 1
fi