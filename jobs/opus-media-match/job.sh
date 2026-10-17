#!/usr/bin/env bash
# GitHub runner entry point: try to install OCR tools (tesseract + pdftoppm),
# then run job.py. If the install fails the job still runs, without OCR, and
# SUMMARY.json reports how many files still need OCR.
set -uo pipefail
if [ "${JOB_OCR:-1}" != "0" ] && ! command -v tesseract >/dev/null 2>&1 && command -v apt-get >/dev/null 2>&1; then
  echo "Installing tesseract-ocr and poppler-utils for OCR ..."
  sudo apt-get update -qq && sudo apt-get install -y -qq tesseract-ocr poppler-utils >/dev/null \
    || echo "OCR tools could not be installed; continuing without OCR."
fi
exec python "${JOB_DIR:-$(dirname "$0")}/job.py"
