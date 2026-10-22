# Running Pinakes on the owner's PC

GitHub's runner has 2 CPUs; OCR is CPU work, so a 24-thread PC finishes the whole ProQuest set in well under an hour
where GitHub needs several daily runs. Progress is never lost either way: both read the last committed
`output/ORDERS.csv` and `output/texts/` and OCR only files that have no text yet, so a PC run and a GitHub run can
overlap, and whichever commits later carries the other's texts forward.

## One command

In PowerShell, inside the repository clone, on the branch you want the results on:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File jobs\pinakes-proquest-ingest\run_on_pc.ps1
```

The script installs Tesseract and Poppler through winget if they are missing, runs the job with every CPU thread
(`-Workers N` to limit it, `-Pages N` to cap OCR pages), writes into `jobs/pinakes-proquest-ingest/output/`, commits
that folder and pushes (`-NoPush` to skip the push). Reruns resume.

## No clone yet

The repository is several GB, so clone only what this needs:

```powershell
git clone --filter=blob:none --sparse https://github.com/D3m0sthene5/Executive-Orders.git
cd Executive-Orders
git sparse-checkout set jobs HANDOFF .github "ProQuest Pre-1937 Orders" research/pre-1937-sources research/stage15/CENSUS research/stage19/code
git checkout corps-of-discovery-lewis-clark
```

## For a Claude desktop-app chat with the computer linked

Paste this:

> In the Executive-Orders repository on this computer (clone it sparsely per jobs/pinakes-proquest-ingest/PC_RUN.md if
> there is no clone), check out branch corps-of-discovery-lewis-clark, pull, and run
> `powershell -ExecutionPolicy Bypass -File jobs\pinakes-proquest-ingest\run_on_pc.ps1`. Do not read the PDFs or the
> texts; report only output/REPORT.md when it finishes. If tesseract or pdftoppm cannot be installed by the script,
> stop and tell me.

If a GitHub run of the same job is still in progress when the PC results are pushed, cancel it from the Actions tab
(or let it finish; its commit will carry the PC texts forward and add nothing new).
