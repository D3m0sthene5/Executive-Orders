# 05 - Platform: is GitHub the wrong place, and what to use instead or alongside

Researched 2026-11-06. Pages marked "opened" were fetched this session. Items marked UNVERIFIED are recalled from memory or came from a page that did not load. The web-search budget ran out partway, so forum coverage (HN, Reddit) is thin: I found two useful HN threads and no Reddit threads. I found no first-hand report of a research pipeline that hit GitHub's 10 GB cap.

## Bottom line

GitHub is the wrong place for the data and the right place for the code, notes, manifests and coordination. Three of the pain points have different causes and different fixes:

1. **Repo size.** GitHub's documented hard cap is 10 GB on-disk. This repo is at 8.4 GB local and about 9 GB on GitHub, so it has roughly 1 GB of headroom. The fix is to stop committing bulk files to git and keep a hash manifest in git instead. This costs about $2 a month.
2. **6-hour job limit and serial execution.** The 6-hour limit applies only to GitHub-hosted runners. Self-hosted runners get 5 days. Serial execution is mostly the repo's own design (the per-branch queue and the freshness guard), not a GitHub limit: free accounts allow 20 concurrent jobs. A self-hosted runner removes the 6-hour limit. It does not remove the freshness guard.
3. **Slow downloads.** Faster runners probably will not help. Jobs are limited by per-host rate limits and robots.txt courtesy, which the project sets itself. A faster runner would also not fix the Claude/GPT session collisions, which are a coordination problem that no platform in this scope addresses.

Unknown that changes the cost math: whether the repo is public. Standard hosted runners are free in public repos. If it is public, every runner alternative below costs money to gain only the longer time limit and more concurrency.

## 1. GitHub's own limits (all opened 2026-11-06)

- **Repository size** ([repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits)): 10 GB maximum on-disk size of the `.git` folder. The page's remedy is Git LFS for binaries and object storage for generated files. Recommended limits: 1 MB per file, 3,000 entries per directory, 5,000 branches. Enforced limits: 2 GB per push, 100 MB per file. Recommended fetch rate is about 15 per second per repo.
- **Guidance** ([large files](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)): keep repos "ideally under 1 GB," "strongly recommend" under 5 GB. Repos that strain infrastructure "may" get a support email asking for corrective action. "Git isn't a backup tool." The page tells users to put large databases in a file-sharing service. What GitHub does to a repo between 10 GB and "hard stop" is not documented; I found no report either way. Treat 10 GB as a wall.
- **Actions limits** ([limits reference](https://docs.github.com/en/actions/reference/limits)): hosted job 6 hours; self-hosted job 5 days; workflow run 35 days. Concurrent jobs on standard runners: 20 (Free), 40 (Pro), 60 (Team), 500 (Enterprise). Artifact storage: 500 MB (Free), 1 GB (Pro), 2 GB (Team); cache 10 GB per repo; support cannot raise storage limits. Artifact retention default 90 days ([docs](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/remove-workflow-artifacts)). `GITHUB_TOKEN` API limit: 1,000 requests per hour per repo. Self-hosted jobs cancel after 24 hours in queue.
- **Consequence for 20 GB downloads:** the 500 MB artifact and 10 GB cache limits mean a hosted job cannot hand 20 GB to the next job through GitHub. It must write to external storage or commit to git. This is probably the root cause of "data committed to git." Standard hosted runner disk size is UNVERIFIED (recalled as about 14 GB free on the 2-core Linux image, which would also force streaming or external storage).
- **Prices** ([runner pricing](https://docs.github.com/en/billing/reference/actions-runner-pricing), rates as of Jan 2026 after the up-to-39% cut, [changelog](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)): Linux 2-core $0.006 per minute; larger runners 4-core $0.012, 8-core $0.022, 16-core $0.042, 32-core $0.082, 64-core $0.162. Larger runners need a Team or Enterprise organization and never draw on included minutes. Included compute is $12 (Free) or $18 (Pro/Team) per month, roughly 2,000 or 3,000 Linux minutes. Storage beyond allowance: $0.25 per GB-month for artifacts, $0.07 per GB-month for cache ([billing](https://docs.github.com/en/billing/concepts/product-billing/github-actions)).
- **Self-hosted runner fee:** GitHub announced a $0.002 per minute platform charge starting 2026-03-01, then postponed it with no new date ([changelog](https://github.blog/changelog/2025-12-16-coming-soon-simpler-pricing-and-a-better-experience-for-github-actions/)). It could return; $0.002 times 12,000 minutes would be $24 a month.
- **Git LFS** ([billing](https://docs.github.com/en/billing/concepts/product-billing/git-lfs)): free quota 10 GiB storage and 10 GiB bandwidth on Free/Pro, 250 GiB each on Team. Prepaid data packs were removed; billing is now metered, and the page gives no per-GiB rate. The older rate (about $0.07 per GiB-month storage, $0.0875 per GiB bandwidth) is UNVERIFIED. The repo already stores a 2.97 GB archive and a 207 MB release in LFS (`MIGRATION_STATUS.md`). Each CI checkout that pulls LFS counts against bandwidth.
- **GitHub Pages** ([limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits)): site no larger than 1 GB, soft 100 GB per month bandwidth, deployments time out after 10 minutes.

## 2. Faster and cheaper Actions runners

None of these changes the 6-hour limit unless it states otherwise, and none changes upstream rate limits. All are drop-in (`runs-on:` label change) except RunsOn and self-hosted, which need AWS or a server.

Cost per 1,000 minutes of a 2 vCPU Linux runner (the unit comparison; GitHub $6.00):

| Provider | Per 1,000 min | Free tier | Page opened |
|---|---|---|---|
| GitHub hosted 2-core | $6.00 | 2,000-3,000 min on private repos | yes |
| Blacksmith 2 vCPU | $4.00 | 3,000 min per month | [pricing](https://www.blacksmith.sh/pricing) |
| WarpBuild 2 vCPU | $4.00 (BYOC $2.00) | credit, amount not stated | [pricing](https://www.warpbuild.com/pricing) |
| Namespace | about $1.00 to $2.00 per vCPU-hour unit, tables conflict | none; Developer plan pay-as-you-go, 3-hour max job | [pricing](https://namespace.so/pricing) |
| Ubicloud 2 vCPU | $1.20 standard, $2.00 premium | 1,250 min per month | [page](https://www.ubicloud.com/use-cases/github-actions) |
| Depot | $6.00 beyond plan; $20 per month for 2,000 min, $200 for 20,000 | none | [pricing](https://depot.dev/pricing) |
| RunsOn (your AWS) | about $0.9 compute (spot, 2 CPU) plus license | free for non-commercial personal projects | [pricing](https://runs-on.com/pricing/) |
| Hetzner VPS self-hosted | flat | n/a | [Hetzner](https://www.hetzner.com/cloud/regular-performance/) |

- **Blacksmith.** Managed runners, 2x faster hardware claimed, 4x faster cache. Also sells "sticky disks" at $0.50 per GB-month, which persist a disk between jobs and could hold a corpus. The "67% savings" figure on the page assumes a 2x runtime reduction and is vendor math. Max job time and artifact limits are not stated on the page.
- **Depot.** Launched as a Docker-build accelerator; its HN thread ([item 39930908](https://hn.algolia.com/api/v1/items/39930908)) has the Depot founder saying the aim is "speed over price," about half GitHub's cost. A commenter said Ubicloud is about 10x cheaper. Depot's own pricing page shows the same $0.006 per minute as GitHub beyond the plan.
- **Namespace.** The page contradicts itself ($0.001 vs $0.002 per vCPU-minute); I would confirm before relying on it. Notable for volume-snapshot cache storage and 24-hour max duration only on the $250 Business plan; the 3-hour Developer limit is below the 6 hours already hit.
- **Ubicloud.** Open-source cloud with the lowest hosted rate found. Standard tier is 1,250 free minutes per month. Maturity and reliability: only the HN comment above; no measured report found.
- **WarpBuild.** Fixed per-minute rates, BYOC mode at $0.002 per minute where cache is free. "Unlimited concurrency" is a marketing line.
- **RunsOn** ([HN launch thread](https://hn.algolia.com/api/v1/items/39930908)). Runs ephemeral spot runners in your own AWS account; license €300 per year (Starter, up to 50,000 jobs per month), free for non-commercial personal use with a link back. Control plane about $7 per month. Inside AWS, S3 transfer in the same region is free and inbound internet traffic is free, so 20 GB downloads cost no bandwidth. The thread's warning about similar DIY setups (Philips Labs Terraform): API rate-limit exhaustion and runners killed early. Spot interruption of a multi-hour job is a real risk and no commenter measured it.
- **Self-hosted on a VPS.** Hetzner Regular Performance, EU: CPX32 (4 vCPU, 8 GB, 160 GB NVMe, 20 TB traffic) €35.99 per month; CPX42 (8 vCPU, 16 GB, 320 GB) €69.99. US (Ashburn, Hillsboro) is much dearer for less: CPX31 €62.99 with 3 TB traffic. Self-hosted jobs run up to 5 days, the disk holds the 20+ GB working set between runs, and a warm clone avoids re-fetching 9 GB. Danger: never attach a self-hosted runner to a public repo that accepts pull requests from forks.

Evidence quality: all savings numbers on vendor pages and on aggregator posts ([Tenki 2026 comparison](https://www.tenki.cloud/blog/github-actions-runner-pricing-2026), itself a vendor) are vendor claims. I found no independent benchmark of download-heavy jobs. Download-bound work does not speed up from faster CPUs.

**Fit and verdict.** The 6-hour limit is fixed only by self-hosted (VPS or RunsOn). Verdict for managed runners (Blacksmith, Depot, Namespace, WarpBuild, Ubicloud): SKIP, they do not address a bottleneck this project has. Verdict for self-hosted on a Hetzner VPS or RunsOn: TRY for the few jobs that exceed or approach 6 hours, after confirming the repo's visibility.

## 3. Data versioning and dataset hosting

- **Git LFS (GitHub).** See section 1. Already used. HN commenter kortex calls git-lfs "a nightmare" because files can be in pointer or binary states and "force history rewrites" ([HN 33047634](https://hn.algolia.com/api/v1/items/33047634)). Bandwidth billing counts each CI clone. Verdict: SKIP for more data; do not make the problem larger.
- **DVC.** Git-linked data versioning with pointer files and a remote (S3, R2, etc.). In November 2025 lakeFS acquired the open-source project from Iterative and says it "will continue as an independent open source tool" for smaller datasets ([announcement](https://lakefs.io/media-mentions/lakefs-acquires-dvc-uniting-data-version-control-pioneers/)). Complaints: indexing took "many minutes" per `dvc status` with many files; slow beyond a few thousand tracked files; no parallel stages; atomic outputs, so a large directory is wiped each run ([HN 41888937](https://hn.algolia.com/api/v1/items/41888937), [GoCardless report](https://home.mlops.community/public/blogs/experience-report-data-version-control-dvc-for-machine-learning-projects)). About 20,000 source texts is the many-small-files case. Verdict: SKIP; a hash manifest plus object storage gives the same guarantee with less machinery.
- **lakeFS.** Git-like branches over S3-style storage. Team plan $499 per month, 5 users, 500 GB ([pricing](https://lakefs.io/pricing/)); managed cloud only at Enterprise price. Verdict: SKIP, wrong scale.
- **Dolt and DoltHub.** SQL database with git semantics (branch, merge, diff by row and cell). DoltHub Pro is $5 per month for private data between 100 MB and 5 GB, then $1 per GB; public databases are free ([announcement 2026-04-24](https://dolthub.com/blog/2026-04-24-announcing-dolthub-pro-for-5-dollars-per-month/)). A DoltHub pricing page could not be read this session. Fit: the register of findings, claims and owner questions (tens of thousands of rows) is where row-level merge would replace CSV/JSONL merge conflicts. It would not hold source texts. Cost to adopt: a few days to move the register and rewrite writers. HN commenter nerdponx recommends Dolt for row-level diffs. No report found of anyone using it for multi-agent writes. Verdict: WATCH; a two-week pilot on a copy of the claim register only if merge conflicts on CSV/JSONL data (not on markdown notes) are confirmed as the main collision.
- **Hugging Face Hub** ([storage limits](https://huggingface.co/docs/hub/storage-limits), [pricing](https://huggingface.co/pricing)). Dataset repos are Git-backed with Xet chunk-level deduplication. Free accounts: 100 GB private, public storage "best-effort"; PRO ($9 per month) up to 10 TB public, 1 TB private; extra public storage $12 per TB per month. No hard per-repo limit; files under 200 GB; under 100,000 files per repo, under 10,000 per folder (20,000 source texts need sharding into subfolders or JSONL/Parquet). Commits degrade "after a few thousand," so batch uploads. Strongest use: publishing the finished dataset with a dataset card and viewer. Not suited as the working store with 93 jobs committing.
- **HF Storage Buckets** ([blog, 2026-03-10](https://huggingface.co/blog/storage-buckets)). Non-versioned, mutable storage on Hub with Xet dedupe; `hf buckets sync` with plan/apply. Included in existing storage plans. Fit: scratch space for intermediate downloads and OCR outputs. Five months old, no CI-specific documentation, no numeric limits stated. Verdict: WATCH; R2 does the same thing with a plainer contract.
- **Oxen.ai.** Data-repo tool; its maintainer says DVC was "painfully slow" ([HN 41888937](https://hn.algolia.com/api/v1/items/41888937)). Pricing page ([opened](https://www.oxen.ai/pricing)): free 50 GB storage and transfer; $30 per month for 100 GB. The page now leads with model inference and GPUs, so the company's focus has moved to AI model hosting. Verdict: SKIP.
- **git-annex / DataLad.** git-annex pointers with pluggable remotes, with one HN commenter (jefurii) reporting 10 years and 40 TB of use as "rock solid." Not opened further; search budget ran out. Verdict: WATCH as the free, mature alternative to DVC if pointer-file semantics are wanted.

## 4. Object storage (the central fix)

| Service | Storage | Egress | Operations | 100 GB cost per month |
|---|---|---|---|---|
| [Cloudflare R2](https://developers.cloudflare.com/r2/pricing/) | $0.015 per GB-month (10 GB free) | free | Class A $4.50 per million, Class B $0.36 per million | $1.35 after free tier |
| [Backblaze B2](https://www.backblaze.com/cloud-storage/pricing) | from $6.95 per TB-month (10 GB free) | free up to 3x stored data, then $0.01 per GB; free via CDN/compute partners | Class A/B/C free | $0.70 |
| AWS S3 Standard | about $0.023 per GB-month (UNVERIFIED, table did not load) | about $0.09 per GB to internet, 100 GB per month free; free to EC2 in same region ([page](https://aws.amazon.com/s3/pricing/)) | metered | about $2.30 |

At this scale all three cost under $3 a month. The deciding factors are egress and tooling. R2 has no egress fee, so downloading 20 GB to a GitHub runner, a Hetzner box or a collaborator's laptop costs nothing, and R2 speaks the S3 API, which DuckDB, rclone, DVC and boto3 all use. A 20 GB pull from S3 to a non-AWS runner would cost about $1.80 per run. B2 is the cheapest per GB and a good second copy.

**Fit:** this removes the pressure on the 10 GB cap, the 500 MB artifact limit and LFS bandwidth. Design that preserves the project's evidence standard: store each source file under its SHA-256 (content-addressed key), and commit a manifest (path, size, SHA-256, origin URL, retrieval date) to git. Claims already cite hash plus byte span, so verification is unchanged. Keep a second copy in B2 and a citable snapshot in Zenodo (section 7) so custody does not depend on one vendor account.

**Migration cost of leaving git:** about 1 to 3 days to write the upload/manifest tooling and change jobs to fetch by hash. Shrinking the existing `.git` requires `git filter-repo` and a force-push, which changes every commit hash. Commit hashes are cited in `MIGRATION_STATUS.md` and probably in the register. A safer path is a new slim repo for ongoing work, with the old repo kept read-only as the frozen evidence archive that new records cite by commit. Run `git-sizer` first to see which paths hold the bytes.

**Verdict:** ADOPT NOW (R2 primary, B2 mirror).

## 5. Compute and orchestration

- **Modal** ([pricing](https://modal.com/pricing)). Serverless Python functions. CPU $0.0000131 per core-second (about $0.047 per core-hour), memory $0.00000222 per GiB-second (about $0.008 per GiB-hour). Starter plan: $30 free credit per month, 100 containers, 3 seats. Volumes $0.09 per GiB-month, 1 TiB per month free. Worked example (my arithmetic): a 4-core, 16 GiB job running 2 hours costs about $0.63; 100 such jobs a month is about $63 minus the $30 credit. Fan-out across 100 containers removes the serial queue entirely. Maximum function timeout is not on the page (UNVERIFIED, recalled as 24 hours). Costs: each of 93 jobs must be wrapped as a function and image; downloads would come from shared cloud IPs that govinfo or HathiTrust may rate-limit differently. For OCR, GPU jobs bill per second. Verdict: TRY on one OCR or re-download job.
- **RunPod** ([pricing](https://www.runpod.io/pricing)). GPU-focused (serverless L4 $0.75 per hour, A100 $2.72 per hour); network volumes $0.07 per GB-month. CPU pods are not on the page. Relevant only for GPU OCR of 1930s-1990s scans. Verdict: WATCH, pair with a GPU OCR tool if one is chosen (covered by other scopes).
- **Coiled** ([pricing](https://www.coiled.io/pricing)). Runs Dask on your AWS/GCP account; $0.05 per CPU-hour platform fee, free tier $25 of usage per month. Assumes Dask workloads. Verdict: SKIP.
- **Ray / Anyscale.** Pricing not opened. Built for ML clusters; the jobs here are I/O-bound downloads and text checks. Verdict: SKIP.
- **Prefect** ([pricing](https://www.prefect.io/pricing)). Hobby tier free forever: 2 users, 5 deployments, 500 serverless minutes per month, 7-day run retention. Verdict: SKIP; adds a scheduler on top of jobs whose problem is data placement.
- **Dagster** ([pricing](https://dagster.io/pricing)). Solo $10 per month plus $0.040 per credit (one credit per asset materialization or op). Its asset model (each order or batch as a partitioned asset with lineage and staleness tracking) matches the freshness-guard logic, but converting 93 jobs is weeks of work. Verdict: WATCH.
- **Kestra** ([pricing](https://kestra.io/pricing)). Open source core free; self-hosted server. Verdict: SKIP.
- **Airflow, Hamilton.** Not opened this session. Airflow is heavy to self-host for one researcher; Hamilton (Python function DAGs) is a library, not a scheduler. Verdict: SKIP.

None of the orchestrators fixes agent-session collisions. Those happen in notes and PRs, not in job scheduling.

## 6. Query and publishing

- **DuckDB** ([R2 import guide](https://duckdb.org/docs/stable/guides/network_cloud_storage/cloudflare_r2_import.html) exists; contents not read). Query Parquet or JSONL directly from R2 or S3 without loading into a server. Free, mature. Convert the tens of thousands of JSONL records to Parquet once per release; DuckDB-WASM can then query it in the browser from a static site. Verdict: ADOPT NOW for analysis and checking; zero cost.
- **MotherDuck** ([pricing](https://motherduck.com/product/pricing/)). Hosted DuckDB; Lite is free (10 GB, 10 hours compute per month, 3 users); Business $250 per month. Verdict: SKIP, DuckDB local is enough at this size.
- **SQLite and Datasette.** The project already ships a canonical SQLite (Stage 17). Datasette is Apache 2.0 but its 1.0 line is still alpha (1.0a41, 2026-09-24; stable 0.65.5) per [datasette.io](https://datasette.io/). It publishes via Cloud Run, Heroku or Vercel, so it needs a server. Datasette Lite (SQLite in the browser) was not on the page and I did not verify it. Verdict: WATCH; useful for a public explorer of the register.
- **Observable Framework** ([site](https://observablehq.github.io/framework/)). Free, open-source static site generator; data loaders can be written in Python and run at build time, output is static files that "can be hosted anywhere." Version 1.13.4. This fits the current per-order progress cards: a build step reads the manifest and Parquet and emits pages, and no database server is needed. Verdict: TRY, rebuild one section of the dannykind.wiki progress site with it.
- **Evidence.dev** ([site](https://evidence.dev/)). Open-source SQL-and-markdown BI; the page does not mention DuckDB (my recall says it uses DuckDB, UNVERIFIED); hosted tier prices not listed. Verdict: WATCH, overlaps with Observable Framework.
- **Quarto** ([GitHub Pages guide](https://quarto.org/docs/publishing/github-pages.html)). Use `freeze: auto` so computed results are committed and only changed documents re-run; do not commit `_site`. Fit: the replication appendix and the law-review article's data supplement, not the order cards. Verdict: TRY for the article companion.
- **Hosting the HTML site.** GitHub Pages: 1 GB site cap, 10-minute deploy timeout. Cloudflare Pages free plan ([limits](https://developers.cloudflare.com/pages/platform/limits/)): 20,000 files per site, 25 MiB per asset, 500 builds per month. About 15,000 order cards each as its own HTML file would sit near the 20,000-file cap once indexes, assets and per-order JSON are added. Build one page per batch or serve per-order data as shards.

## 7. Citable archival releases

- **Zenodo** ([quota](https://help.zenodo.org/docs/deposit/manage-quota/), [records](https://help.zenodo.org/docs/deposit/about-records/)). Free. 50 GB default per record, self-service raising to a 150 GB total allowance. After publication, "Files and the persistent identifier CANNOT be modified"; a new version is a separate record with its own metadata, files and identifier. A concept DOI that covers all versions is UNVERIFIED on the pages read. Fit: one Zenodo version per stage release gives the law review an immutable, citable dataset, which matches the "reproducible dataset" goal. Verdict: ADOPT NOW for each public release.
- **Harvard Dataverse** ([third-party summary](https://jwatte.com/blog/harvard-dataverse-research-data-repository.md), [Dataverse guide](https://guides.dataverse.org/en/latest/user/dataset-management.html)). 2.5 GB per file, up to 1 TB free, DataCite DOI under 10.7910, versioned datasets with one persistent identifier, and a public tombstone instead of deletion. The Harvard page itself did not load; the figures come from a blog post and are UNVERIFIED against Harvard. Verdict: WATCH, a good second DOI mirror if a law-review editor prefers a university repository.
- **OSF** ([HMS summary](https://datamanagement.hms.harvard.edu/share/data-repositories/open-science-framework)). 50 GB public projects, 5 GB private, 5 GB per file; DataCite DOIs for projects but "does not currently support DOI versioning." Verdict: SKIP for the dataset; fine for preregistration-style documents.

## 8. Reports from people who ran pipelines in git

Thin; the search budget ended before I could dig further. What I found:

- DVC users: slowdowns with thousands of tracked files, one-core stages, merge conflicts on lock files ([HN 33047634](https://hn.algolia.com/api/v1/items/33047634), [HN 41888937](https://hn.algolia.com/api/v1/items/41888937)); GoCardless's report says stages cannot run in parallel and `dvc.lock` cannot represent both a full dataset and a CI subset.
- git-lfs: "a nightmare" (kortex, HN 33047634).
- Self-hosted runner builders: the Philips Labs Terraform setup exhausts GitHub's API rate limit and loses runners; ECS or Karpenter-based setups take time to tune ([HN 39930908](https://hn.algolia.com/api/v1/items/39930908)).
- Depot's co-founder notes GitHub's 10 GB cache limit makes layer caching impractical (same thread).
- Not found: Simon Willison's "git scraping" posts are the best-known case of data in git; they did not surface a size-limit story in my results, and I did not open them.

## 9. Migration options at this project's scale

Assumptions: 100 GB total corpus (9 GB repo plus scans and source PDFs); 100 job runs a month averaging 2 hours (12,000 minutes of 2-core runner time); 20 GB download per run. Actual job minutes were not available to me; scale the compute lines by real usage.

| Option | Monthly cost | Fixes | Does not fix |
|---|---|---|---|
| A. Stay as is | $0 if public repo; about $72 if private beyond free minutes, plus LFS overage | nothing | cap risk, 6-hour limit, serial queue |
| B. A plus R2 storage, B2 mirror, Zenodo releases, manifest in git | about $2 | repo size and cap risk, LFS bandwidth, artifact limit, citable releases | 6-hour limit, serial queue, collisions |
| C. B plus Hetzner VPS self-hosted runner(s) (EU CPX32, €36) | about $40 | 6-hour limit (5 days), disk for 20+ GB, per-minute cost, warm cache | per-host rate limits, session collisions, public-repo security rule |
| D. B plus RunsOn on AWS | about $45 to $55 (about €25 license, $7 control plane, about $16 spot compute) | 6-hour limit, concurrency, free in-region S3 | spot interruption of long jobs, same upstream limits |
| E. B plus Modal fan-out for heavy jobs | about $30 to $60 (about $63 at 100 two-hour jobs, less the $30 credit) | serial queue, 6-hour limit, parallel OCR | rewrite effort, shared-IP rate limits |
| F. B plus Blacksmith or Ubicloud | $14 (Ubicloud) to $36 (Blacksmith after free minutes) | per-minute price only | 6-hour limit (unverified), downloads |
| G. Leave GitHub for GitLab or Codeberg | not researched | n/a | outside the brief; the problem is data placement, not host |

Recommended sequence: B first (days, about $2), then C or D only for the long jobs once real job durations are measured, then E for OCR if scans prove to be the bottleneck.

## Ranked top 5 for this scope

1. **Cloudflare R2 with a B2 mirror and a SHA-256 manifest in git** — ADOPT NOW. Removes the 10 GB cap risk for about $2 a month and keeps byte-span verification intact.
2. **Zenodo versioned releases** — ADOPT NOW. Free, immutable, versioned DOIs for each public release; matches the law-review citation need.
3. **DuckDB over Parquet on R2** — ADOPT NOW. Zero cost, lets checkers and the site query records without a server.
4. **Self-hosted runner on a Hetzner VPS (or RunsOn)** — TRY for the few jobs near the 6-hour limit, after confirming the repo's visibility.
5. **Observable Framework for the progress site** — TRY on one section; a Modal pilot for OCR fan-out is the next candidate if scans dominate runtime.

## Considered and rejected

Managed runners (Blacksmith, Depot, Namespace, WarpBuild, Ubicloud) for pure speed, because downloads are rate-limited by the sources. lakeFS ($499 per month). Oxen.ai (pivoted to model hosting). Coiled, Ray/Anyscale (cluster tools for Dask/ML). Prefect, Kestra, Airflow, Hamilton (no data-placement benefit). MotherDuck (DuckDB local is enough). OSF as dataset host (no DOI versioning, 50 GB cap). More Git LFS (bandwidth billing, history-rewrite risk).

## Gaps

Repo visibility and real job minutes unknown. Hosted runner disk size, LFS per-GiB rate, Modal max timeout, Harvard's own limits, S3 list price, Datasette Lite and DataLad were not verified from primary pages. GitHub star counts could not be fetched because the `gh` CLI was restricted to this session's repos. Forum coverage is thin.
