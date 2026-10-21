# Pinakes HTR on the owner's PC: read the ProQuest scans that failed Pinakes's text screen again three ways (tesseract at
# 300 dpi, Microsoft's TrOCR handwriting model, a local vision-language model), line the readings up word by word,
# then commit the results. Everything runs on this machine's GPU.
# Run from anywhere inside the repository clone, in PowerShell:
#   powershell -ExecutionPolicy Bypass -File jobs\pinakes-htr\run_on_pc.ps1
# Options: -Limit 10 (read only the first N orders, for a trial), -NoPush (commit only), -NoCommit.
param([int]$Limit = 0, [switch]$NoPush, [switch]$NoCommit)
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

# 1. tesseract and pdftoppm: the same programs Pinakes uses (its run_on_pc.ps1 installs them). A Tesseract unpacked
#    without admin rights into %USERPROFILE%\Tesseract-OCR is found too (not %LOCALAPPDATA%: the Claude desktop app is an
#    MSIX package, and what it writes under AppData is redirected into its private storage).
$tess = Find-Exe "tesseract.exe" @("$env:USERPROFILE\Tesseract-OCR", "$env:LOCALAPPDATA\Programs\Tesseract-OCR", "C:\Program Files\Tesseract-OCR", "C:\Program Files (x86)\Tesseract-OCR")
$pop = Find-Exe "pdftoppm.exe" @("$env:LOCALAPPDATA\Microsoft\WinGet\Packages", "C:\Program Files\poppler", "C:\poppler")
if (-not $tess -or -not $pop) { throw "tesseract.exe or pdftoppm.exe not found; run jobs\pinakes-proquest-ingest\run_on_pc.ps1 first." }
$env:PATH = "$tess;$pop;$env:PATH"

# 2. A private Python environment for the GPU stack (PyTorch with CUDA 12.8 for RTX 50-series cards, transformers).
$venv = "$env:USERPROFILE\.pinakes-htr\venv"
$py = "$venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
  python -m venv $venv
  & $py -m pip install -q --upgrade pip
  & $py -m pip install -q numpy==2.2.6 pillow==11.2.1 pypdf==6.20.1
  & $py -m pip install -q torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
  & $py -m pip install -q transformers==4.52.4 sentencepiece==0.2.0 accelerate==1.7.0
}
& $py -m pip install -q --disable-pip-version-check accelerate==1.7.0   # added for the VLM after first installs
& $py -m pip install -q --disable-pip-version-check torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cu128
& $py -c "import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'none (CPU; slow)')"

# 3. Tests, then the run, straight into the committed output folder; a rerun skips orders already read.
$root = (git rev-parse --show-toplevel)
Set-Location $root
$env:REPO_ROOT = $root
$env:OUTPUT_DIR = Join-Path $root "jobs\pinakes-htr\output"
if ($Limit -gt 0) { $env:HTR_LIMIT = "$Limit" }
Push-Location jobs\pinakes-htr
& $py -m unittest -v test_htr
$tests = $LASTEXITCODE
Pop-Location
if ($tests -ne 0) { throw "tests failed; HTR not run" }
& $py jobs\pinakes-htr\htr.py
if ($LASTEXITCODE -ne 0) { throw "HTR failed" }
& $py jobs\pinakes-htr\vlm.py
if ($LASTEXITCODE -ne 0) { throw "VLM reading failed" }
& $py jobs\pinakes-htr\compare.py
if ($LASTEXITCODE -ne 0) { throw "comparison failed" }

# 4. Commit and push the output folder.
if (-not $NoCommit) {
  git add -A "jobs/pinakes-htr/output"
  git commit -m "Results of job(s): pinakes-htr (owner's PC, $env:COMPUTERNAME)"
  if (-not $NoPush) { git push }
}
Get-Content jobs\pinakes-htr\output\REPORT.md
