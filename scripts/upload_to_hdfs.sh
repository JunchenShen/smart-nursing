#!/usr/bin/env bash
set -euo pipefail

HDFS_URI="${HDFS_URI:-hdfs://namenode:8020}"
HDFS_TARGET_DIR="${HDFS_TARGET_DIR:-/smart-care-training}"
LOCAL_DATA_DIR="${LOCAL_DATA_DIR:-/data}"

required_files=(
  students.csv
  courses.csv
  resources.csv
  learning_events.csv
  assessment_scores.csv
)

echo "Waiting for HDFS at ${HDFS_URI} ..."
for _ in $(seq 1 60); do
  if hdfs dfs -fs "${HDFS_URI}" -ls / >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

hdfs dfs -fs "${HDFS_URI}" -mkdir -p "${HDFS_TARGET_DIR}"

for file in "${required_files[@]}"; do
  if [ ! -f "${LOCAL_DATA_DIR}/${file}" ]; then
    echo "Missing local data file: ${LOCAL_DATA_DIR}/${file}" >&2
    exit 1
  fi
  hdfs dfs -fs "${HDFS_URI}" -put -f "${LOCAL_DATA_DIR}/${file}" "${HDFS_TARGET_DIR}/${file}"
  echo "Uploaded ${file} to ${HDFS_URI}${HDFS_TARGET_DIR}/${file}"
done

echo "HDFS upload completed:"
hdfs dfs -fs "${HDFS_URI}" -ls "${HDFS_TARGET_DIR}"
