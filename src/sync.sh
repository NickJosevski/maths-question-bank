#!/bin/sh
# Pull the exported question bank from the generator repo, then rebuild.
#
#   src/sync.sh [path/to/generator/pipeline/webapp]
#
# The generator - the thing that reads the textbook chapters and produces these
# three JSON files - is a separate, private repo. This repo owns the app; that
# one owns the data. Point this at its webapp/ directory.
set -eu
HERE=$(cd "$(dirname "$0")" && pwd)
FROM=${1:-${MQB_GENERATOR:-$HERE/../../MATHS/pipeline/webapp}}

for f in questions.json extra.json working.json; do
  [ -f "$FROM/$f" ] || { echo "missing: $FROM/$f" >&2; exit 1; }
done
for f in questions.json extra.json working.json; do
  cp "$FROM/$f" "$HERE/$f"
  echo "  <- $f"
done
exec python3 "$HERE/build.py"
