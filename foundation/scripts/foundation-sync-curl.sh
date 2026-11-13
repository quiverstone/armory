#!/usr/bin/env bash
# Download the Quiverstone foundation templates listed in foundation/scripts/foundation_files.txt.
#
# Environment:
#   ASSET_BASE_URL  public asset host (default: https://armory.quiverstone.io, CloudFront in front of the
#                   armory.quiverstone.io bucket). To bypass CloudFront use the S3 endpoint:
#                   ASSET_BASE_URL=https://s3.us-east-2.amazonaws.com/armory.quiverstone.io ./foundation-sync-curl.sh
#   LOCAL_DIR       download directory (default: ./foundation)
set -euo pipefail

ASSET_BASE_URL="${ASSET_BASE_URL:-https://armory.quiverstone.io}"
KEY_LIST_KEY="foundation/scripts/foundation_files.txt"
LOCAL_DIR="${LOCAL_DIR:-./foundation}"
LOCAL_KEY_LIST="$(mktemp)"
trap 'rm -f "${LOCAL_KEY_LIST}"' EXIT

echo "Downloading foundation templates from ${ASSET_BASE_URL}"
mkdir -p "${LOCAL_DIR}"

if ! curl -fsS "${ASSET_BASE_URL}/${KEY_LIST_KEY}" -o "${LOCAL_KEY_LIST}"; then
  echo "Error: failed to download ${KEY_LIST_KEY}" >&2
  exit 1
fi
if [[ ! -s "${LOCAL_KEY_LIST}" ]]; then
  echo "Error: ${KEY_LIST_KEY} is empty" >&2
  exit 1
fi

downloaded=0
failed=0
while IFS= read -r key || [[ -n "${key}" ]]; do
  [[ -z "${key}" || "${key}" == \#* ]] && continue
  # Only accept relative keys that stay inside LOCAL_DIR
  if [[ "${key}" == /* || "${key}" == *..* ]]; then
    echo "Skipping unsafe key: ${key}" >&2
    continue
  fi
  url="${ASSET_BASE_URL}/${key}"
  local_path="${LOCAL_DIR}/${key}"
  mkdir -p "$(dirname "${local_path}")"
  if curl -fsS "${url}" -o "${local_path}"; then
    downloaded=$((downloaded + 1))
  else
    echo "Failed to download: ${key}" >&2
    failed=$((failed + 1))
  fi
done <"${LOCAL_KEY_LIST}"

echo "Downloaded ${downloaded} file(s), ${failed} failed, to $(cd "${LOCAL_DIR}" && pwd)"
[[ "${failed}" -eq 0 ]]
