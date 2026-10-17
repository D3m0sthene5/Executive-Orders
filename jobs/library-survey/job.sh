#!/usr/bin/env bash
set -euo pipefail
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ghostscript tesseract-ocr >/dev/null
python "$(dirname "$0")/job.py"
