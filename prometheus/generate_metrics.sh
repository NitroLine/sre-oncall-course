#!/bin/bash
# Adjust as needed.
TEXTFILE_COLLECTOR_DIR=/home/ubuntu/sre-oncall-course/metrics
LOG_FILE_PATH=/home/ubuntu/sre-oncall-course/logs/access.log


COUNT_LOGS_LINES=$(/usr/bin/wc -l < $LOG_FILE_PATH)
# Write out metrics to a temporary file.
cat << EOF > "$TEXTFILE_COLLECTOR_DIR/access_count.prom.$$"
# HELP oncall_requests_total Number of requests to oncall based on access logs
# TYPE oncall_requests_total counter
oncall_requests_total $COUNT_LOGS_LINES
EOF

# Rename the temporary file atomically.
# This avoids the node exporter seeing half a file.
mv "$TEXTFILE_COLLECTOR_DIR/access_count.prom.$$" \
  "$TEXTFILE_COLLECTOR_DIR/access_count.prom"
