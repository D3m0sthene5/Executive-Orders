# Pinakes on the owner's PC: OCR the ProQuest PDFs on every core, then commit the results so the GitHub
# runs carry them forward. Run from anywhere inside the repository clone, in PowerShell:
#   powershell -ExecutionPolicy Bypass -File jobs\pinakes-proquest-ingest\run_on_pc.ps1
# Options: -Workers 20 (default: every CPU thread), -Pages 100000 (OCR page budget), -NoPush (commit only).
param([int]$Workers = 0, [int]$Pages = 100000, [switch]$NoPush)
$ErrorActionPreference = "Stop"

function Find-Exe($name, $roots) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if ($cmd) { return Split-Path $cmd.Source }
  foreach ($r in $roots) {
    if (Test-Path $r) {
      $hit = Get-ChildItem -Path $r -Recurse -Filter $name -ErrorAction SilentlyContinue | Select-Object -First 1
      if ($hit) { return $hit.DirectoryName }
    }
  }
  return $null
}

# 1. OCR programs (tesseract and poppler's pdftoppm), installed once through winget if missing.
$tess = Find-Exe "tesseract.exe" @("C:\Program Files\Tesseract-OCR", "C:\Program Files (x86)\Tesseract-OCR")
if (-not $tess) {
  winget install -e --id UB-Mannheim.TesseractOCR --accept-source-agreements --accept-package-agreements
  $tess = Find-Exe "tesseract.exe" @("C:\Program Files\Tesseract-OCR", "C:\Program Files (x86)\Tesseract-OCR")
}
$pop = Find-Exe "pdftoppm.exe" @("$env:LOCALAPPDATA\Microsoft\WinGet\Packages", "C:\Program Files\poppler", "C:\poppler")
if (-not $pop) {
  winget install -e --id oschwartz10612.Poppler --accept-source-agreements --accept-package-agreements
  $pop = Find-Exe "pdftoppm.exe" @("$env:LOCALAPPDATA\Microsoft\WinGet\Packages", "C:\Program Files\poppler", "C:\poppler")
}
if (-not $tess -or -not $pop) { throw "tesseract.exe or pdftoppm.exe not found; install Tesseract (UB-Mannheim) and Poppler and rerun." }
$env:PATH = "$tess;$pop;$env:PATH"
python -m pip install --user -q pypdf==6.20.1

# 2. Run the job straight into the committed output folder; prior texts come from git HEAD, so a rerun resumes.
$root = (git rev-parse --show-toplevel)
Set-Location $root
$env:REPO_ROOT = $root
$env:OUTPUT_DIR = Join-Path $root "jobs\pinakes-proquest-ingest\output"
$env:JOB_OCR_PAGES = "$Pages"
if ($Workers -gt 0) { $env:JOB_WORKERS = "$Workers" }
New-Item -ItemType Directory -Force -Path $env:OUTPUT_DIR | Out-Null
python jobs\pinakes-proquest-ingest\job.py
if ($LASTEXITCODE -ne 0) { throw "job failed" }

# 3. Commit and push the results (the output folder is what the GitHub runs and the other jobs read).
git add -A "jobs/pinakes-proquest-ingest/output"
git commit -m "Results of job(s): pinakes-proquest-ingest (owner's PC, $env:COMPUTERNAME)" 
if (-not $NoPush) { git push }
Get-Content jobs\pinakes-proquest-ingest\output\REPORT.md
