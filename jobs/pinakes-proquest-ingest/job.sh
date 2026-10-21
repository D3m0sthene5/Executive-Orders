#!/usr/bin/env bash
# Pinakes: ProQuest PDF ingest with OCR. tesseract and poppler (pdftoppm) come from apt on the runner.
set -euo pipefail
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq tesseract-ocr poppler-utils >/dev/null
python -m pip install -q pypdf==6.20.1
python "$(dirname "$0")/job.py"
