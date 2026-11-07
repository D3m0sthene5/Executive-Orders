# Playfair: a one-section trial of Observable Framework

Named for William Playfair, who invented the line chart and the bar chart (1786). This job builds one section of the
progress site, the project's trajectory, with Observable Framework on GitHub's runner, and measures it. It deploys
nothing and touches no live site. Trial only; written 2026-11-06 for the Encyclopedie campaign.

## What the job does

`job.sh` copies three committed files (`jobs/tsiolkovsky-trajectory/output/TRAJECTORY.csv`, `GENERATION_POINTS.csv`,
`MISSION.csv`) next to the hand-written `src/index.md` and `src/observablehq.config.js`, runs `npm install` with
`@observablehq/framework` pinned to exactly `1.13.4`, runs `observable build`, and writes to `output/`:

- `MEASUREMENTS.json`: install and build seconds, file count, bytes and gzip bytes of `dist/`, bytes by extension, the
  ten largest files, the size of the comparison section, the render check;
- `dist.zip` (234 KB, written because it is under 5 MiB) and `screenshot.png` (197 KB, under the 500 KB limit);
- `build.log`, `npm-install.log`, `BUDGET.json` (committed output 449,010 bytes; limit 20 MiB).

Checks inside the job: the three data files must appear in `dist/` byte for byte (SHA-256); headless Chrome opens the
built page and the job fails unless at least five `svg` elements drew (16 did). This is a build trial, not a
Tier 2 evidence job, so it has no claim fragments and no error-rate controls.

First run: https://github.com/D3m0sthene5/Executive-Orders/actions/runs/42307107988, `output/STATUS.json` says
`succeeded`, exit code 0, commit `483108ae31ed`. (Editing this README reruns the job; the numbers below are from that
first run, and `output/MEASUREMENTS.json` (the branch trial's copy is kept as `TRIAL_MEASUREMENTS_run42307107988.json`) holds the latest.)

## 1. The site, and how close it is to the limits

The survey assumed GitHub Pages or Cloudflare Pages. It is neither.

**Where it is hosted.** `https://dannykind.wiki` answers `308` to `https://www.dannykind.wiki/` with `Server: Vercel`
and `X-Vercel-Id`; DNS nameservers are `ns1.vercel-dns.com` and `ns2.vercel-dns.com`. `gh api
repos/D3m0sthene5/Executive-Orders/pages` returns 404 (no GitHub Pages site), and this repository holds no Pages or
Cloudflare deploy workflow. The Vercel project is `dkla` (team `dbk6`), built from the separate repository
**D3m0sthene5/DKLA** (the Danny Kind Legal Atlas), which is the site's root page. Vercel lists `dannykind.wiki`,
`www.dannykind.wiki` and `dkla.dev` as aliases of the production deployment. The repository `jobs/gessner-cards/README.md`
documents the EO section that is live today: `/eo/gesner`, served by the function `api/eo-gesner.js`, which reads
`jobs/gessner-cards/output/CARDS.html` from `main` on each request (2.71 MB; `/eo` itself redirects to a
`chatgpt.site` page, outside both repositories).

**How it is built.** `vercel.json`: `buildCommand: node tools/build.mjs`, `outputDirectory: dist`. The build assembles
the atlas with Python, then `tools/package-public.mjs` copies an explicit allowlist (`tools/public-files.json`: 341
files and one directory) into `dist/`, plus the generated page `DKLA-v2.8.html` split into per-brief JSON files.

**Size and file count of what is deployed** (measured 2026-11-06; the deployed `dist/` is not downloadable, so this is
the allowlist summed from GitHub's tree sizes plus the generated files measured over HTTP):

| Part | Files | Size |
|---|---|---|
| Allowlisted source files (316 in `added-sources/`: PDFs, DOCX, text) | 537 | 666.6 MiB (`added-sources` alone 659.7 MiB) |
| `DKLA-v2.8.html` (served, `Content-Length` 69,588,065) | 1 | 66.4 MiB |
| `assets/briefs/<sha256>.json`, the split briefs (1,468 records plus the aggregate; `Content-Length` of each) | 1,469 | 26.3 MiB |
| `index.html`, `sw.js`, `version.json` (served) | 3 | 4 KB |
| **Total, estimated** | **about 2,010** | **about 759 MiB (0.74 GiB)** |

The estimate has two soft spots: the `Content-Length` values come from the CDN, and I did not unpack a real `dist/`.
The source tree of the DKLA repository is 33,473 files and 811 MiB (30,227 files under `src/`), of which 136.6 MiB is
outside `added-sources/`.

**Limits, from the providers' documentation:**

| Limit | Value | Source | This site |
|---|---|---|---|
| GitHub Pages: published site size | "may be no larger than 1 GB" | https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits | 759 MiB is 74% of 1 GiB (about 80% of 10^9 bytes). Close, but the site is not on Pages. |
| Cloudflare Pages: files per site | 20,000 (Free); 100,000 on paid plans with `PAGES_WRANGLER_MAJOR_VERSION=4` | https://developers.cloudflare.com/pages/platform/limits/ | about 2,010 files: 10% of 20,000. |
| Cloudflare Pages: size of one asset | 25 MiB | same page | Would fail: `DKLA-v2.8.html` (66.4 MiB) and 10 listed files exceed it (largest 65.9 MiB). |
| Vercel: build output files | "no upper limit for output files created during a build" (builds fail past 45 minutes) | https://vercel.com/docs/limits | Not a constraint. Last production build took 56.0 s (`buildingAt` to `ready` in the deployment record). |
| Vercel: files uploaded by CLI | 15,000 source files; 100 MB (Hobby) or 1 GB (Pro) | same page | Applies to CLI deploys only. This site deploys from Git; its 33,473 source files would exceed 15,000 if it were ever deployed by CLI. |

Plain reading: the site is under every limit that applies to it. It is not on GitHub Pages, whose 1 GB limit it
would approach, and it could not move to Cloudflare Pages unchanged because of the 25 MiB per-file cap. Adding a
section built with Framework (644 KB) is rounding error on any of these limits. I could not see the Vercel plan of team
`dbk6`, so I did not check plan-specific bandwidth or build-minute quotas.

## 2. The Observable version of the section

One page, `src/index.md` (129 lines of Markdown with JavaScript cells). It shows, from the committed Tsiolkovsky
series (21 days, 41 tracker generations):

- four stat cards (work held 6,631 h; share of mission 36.5%; phase Translunar coast; 1,185 ready for human review);
- the work-hours line over time with the low-high sensitivity band, and a checkbox that shows or hides the band (the
  one interactive element; it re-renders the chart in the browser with no server);
- a stacked area of work by step (census, provisional status, original text, clause inventory, and so on), with a
  legend;
- ready and claims as two lines; daily velocity as bars; every tracker generation as dots, placed by landing time;
- a table of the rocket dashboard's milestones (below the cut of the screenshot, so not checked by eye).

`output/screenshot.png` shows the render in headless Chrome (cut off at 2,300 px, so the milestone table is below the
fold of the image). Charts are Observable Plot, which Framework bundles; hovering a point shows a tooltip. The theme is
Framework's default (serif headings, light cards); I did not test it at phone width.

It drew correctly on the first push, with no local preview, because the page is plain Markdown plus short Plot calls.

## 3. Build time and size, against the current section

There is no trajectory page on the live site, so the comparison is the nearest live EO section, the order cards at
`/eo/gesner` (one generated HTML file; its job ran 5 s on 2026-11-06, 22:15:38 to 22:15:43 UTC). That page is cards and
text, not charts, so this compares footprints, not equal pages.

| | Framework section (this trial) | Gessner cards (live) |
|---|---|---|
| Files | 44 (38 JS, 3 CSV, 2 CSS, 1 HTML) | 1 |
| Bytes | 643,767 | 2,708,914 |
| Gzip bytes | 223,742 | 542,158 |
| First page load, by Framework's own count | page 12 kB + imports 598 kB + files 39 kB | the whole file |
| Build | `npm install` 8.2 s + `observable build` 5.2 s = 13.4 s (whole runner job 36 s) | 5 s |
| Toolchain | Node 24.22.2 (preinstalled on the runner), 316 packages, 71.7 MB of `node_modules` | Python standard library |

Of the 598 kB of JavaScript, Observable Plot is 213 kB (72 kB gzip) and the rest is d3 modules, the Framework runtime
and the inputs library. Every file is a static file, so it can sit on any host, including Vercel's `dist/`.

## 4. Maintenance cost

- **A second toolchain.** The project's jobs are Python. Framework needs Node on the runner (present), an npm install on
  every run, and 316 packages. No `package-lock.json` is committed here (I cannot run npm on this PC), so only
  Framework is pinned; its dependencies resolve fresh each run. An adopted section must commit the lockfile.
- **Build-time network.** `build.log` shows the d3 and Plot modules fetched and rewritten into `dist/_npm/`; a CDN or
  registry outage fails the build. The `dist/` itself needs no network at view time.
- **Project health.** Framework's last release is 1.13.4 (2026-03-02); the one before it is 1.13.3 (2025-04-16)
  (npm registry, checked 2026-11-06). Releases are slow. The library is stable, but I would expect to own any
  breakage after a Node or d3 change.
- **Fitting the live site.** `DKLA` publishes only files listed in `tools/public-files.json`, and Framework names its
  files by content hash (`_npm/.../2e9f152c.js`), so every rebuild renames files. It would need a directory entry for
  the section and a decision on where `dist/` lives. The live EO page avoids rebuilds by having a function read
  `main` on each request; a static multi-file `dist/` cannot use that trick without a proxy per file, or a rebuild
  and a push to DKLA each time the data refresh runs. I did not check whether Framework 1.13.4 can serve from a
  sub-path such as `/eo/playfair` (its `base` option); that must be confirmed before adoption.
- **Authoring.** A new chart is about eight lines of Plot in Markdown; people who write Python for this project can
  pick it up, and nobody needs to touch HTML. Compared with building the same HTML by string templates in Python, as
  the cards job does, that is a clear gain for charts.

## 5. Recommendation

**Adopt, narrowly, for chart sections that read committed CSV or JSON time series, and pilot one before any wider
move.** First candidates: the trajectory (this page), the readiness-by-step history, and the Bentham yield and cost
series. These are small data, many charts, and a reader who benefits from hover and toggles.

**Do not adopt for** the order cards, per-order tables and any page that lists all 14,998 orders (a Python-generated
file is simpler and already works), or for the existing DKLA atlas build.

Reasons: it built in 13 s and shipped 644 KB (224 KB gzip), a quarter the size of the existing cards page; the site is
far from every limit that applies to it, so the added bytes do not matter; it rendered correctly with no debugging.
Against it: a Node toolchain beside the Python one, an unpinned dependency tree until a lockfile is committed, a
slow-moving upstream, and one real integration question, how the multi-file `dist/` reaches `dannykind.wiki`. A
cheaper alternative worth a look for the same charts: Plot loaded from a pinned CDN URL inside a Python-generated single
HTML file, which keeps the cards job's no-rebuild pattern but gives up Framework's inputs, layout and theming.

Open question for the owner: where should an Observable section be published (a path inside the DKLA repository, or its
own Vercel project such as `playfair.dannykind.wiki`), and who owns that deploy?
