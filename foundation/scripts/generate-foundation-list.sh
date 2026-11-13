#!/usr/bin/env bash
# Print every publishable file in the repo as keys relative to the repo root, into foundation_files.txt.
# foundation_files.txt is curated: review the diff and keep only the foundation templates before committing.
# Run from foundation/scripts/.
set -euo pipefail

OUTPUT_FILE="foundation_files.txt"
REPO_ROOT="../.."

echo "Generating ${OUTPUT_FILE} from files in ${REPO_ROOT}"
TMP_FILE="$(mktemp)"
trap 'rm -f "${TMP_FILE}"' EXIT

find "${REPO_ROOT}" -type f \
  -not -path "*/.*" \
  -not -path "*/scripts/*" \
  -not -path "*/_archive/*" \
  -not -name ".DS_Store" \
  -not -name "LICENSE" \
  -not -name "README.md" \
  -not -name "${OUTPUT_FILE}" |
  sed "s|^${REPO_ROOT}/||" | LC_ALL=C sort >"${TMP_FILE}"
mv "${TMP_FILE}" "${OUTPUT_FILE}"

echo "Total files added: $(wc -l <"${OUTPUT_FILE}" | tr -d ' ')"
cat "${OUTPUT_FILE}"
