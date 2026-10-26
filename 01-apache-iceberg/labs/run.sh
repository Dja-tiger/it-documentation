#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="${ICEBERG_LAB_CACHE:-${TMPDIR:-/tmp}/iceberg-learning-1.12.0}"
JAR_NAME="iceberg-spark-runtime-3.5_2.12-1.12.0.jar"
IMAGE="apache/spark:3.5.5-java17-python3@sha256:96dc2bada923824300e1ece564389258934655ba6f463d6daff8753ff0c639ce"
JAR_SHA256="8dd8c90e54ed1a20f2461309d047a255ee56382eb7c0a46162b27a4936fd86dc"
mkdir -p "$CACHE_DIR"
CACHE_DIR="$(cd -- "$CACHE_DIR" && pwd)"

if [[ ! -s "$CACHE_DIR/$JAR_NAME" ]]; then
  curl --fail --location --retry 3 \
    "https://repo.maven.apache.org/maven2/org/apache/iceberg/iceberg-spark-runtime-3.5_2.12/1.12.0/$JAR_NAME" \
    -o "$CACHE_DIR/$JAR_NAME.part"
  mv "$CACHE_DIR/$JAR_NAME.part" "$CACHE_DIR/$JAR_NAME"
fi

if command -v sha256sum >/dev/null 2>&1; then
  ACTUAL_SHA256="$(sha256sum "$CACHE_DIR/$JAR_NAME")"
else
  ACTUAL_SHA256="$(shasum -a 256 "$CACHE_DIR/$JAR_NAME")"
fi
if [[ "${ACTUAL_SHA256%% *}" != "$JAR_SHA256" ]]; then
  echo "Iceberg JAR checksum mismatch: $CACHE_DIR/$JAR_NAME" >&2
  exit 1
fi

exec docker run --rm --hostname localhost --network none \
  --env SPARK_LOCAL_IP=127.0.0.1 \
  --mount "type=bind,src=$LAB_DIR,dst=/lab,readonly" \
  --mount "type=bind,src=$CACHE_DIR/$JAR_NAME,dst=/opt/iceberg/$JAR_NAME,readonly" \
  --entrypoint /opt/spark/bin/spark-submit \
  "$IMAGE" --master 'local[2]' \
  --jars "/opt/iceberg/$JAR_NAME" /lab/check.py
