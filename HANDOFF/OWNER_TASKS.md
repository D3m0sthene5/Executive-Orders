# Owner tasks (Photius, 2026-11-06 evening)

Things only the owner can do. Each item says what to do, where the result goes, and what it unlocks. The earlier
microfilm item (the 2026-10-19 "do not plan around the reel set" rule) is replaced by items 1 and 2 for NARA M1118 under
decision D-20261106-photius-p5; NYU Film 709 and HeinOnline stay under Kean ask A-20261106-dagron-nyu and the Hein rules.

## 1. Email NARA New York about M1118 (self-service scanning)

NARA Microfilm Publication M1118, "Executive Orders 1–7531, 1862–1936" (RG 11), is the public-domain witness copy of
the numbered series the project will hold. Its roll list is not online (`research/photius/M1118_ROLLS.md`: the only
anchor found is EO 5826 on roll 13; archives.gov/nyc now points to Philadelphia, and a 2024 notice says NYC records were
moved to Kansas City and Philadelphia, so the New York research room may no longer hold microfilm).

Send to newyork.archives@nara.gov (and, if it bounces or redirects, philadelphia.archives@nara.gov, 215-305-2044):

> Subject: Microfilm Publication M1118 (Executive Orders 1–7531, RG 11): roll list and self-service access
>
> I am compiling the lifecycle of every numbered executive order from 1862. Does your research room hold M1118, and may
> I read and scan rolls there myself? Could you send the roll list (the descriptive pamphlet, or the roll breakdown by
> order number and year) for the rolls covering orders 1–4305 (1862–1925)? If the rolls are not held in New York, which
> facility holds them, and is a digitized copy of any roll already available?

Drop the reply in `research/owner-inbox/nara/` (git-ignored) and paste the roll list into
`research/photius/M1118_ROLLS.md`.

## 2. Order digitized M1118 rolls for 1862–1925

NARA sells digitized microfilm rolls at $125 per roll (U.S.; $135 international; eservices.archives.gov/orderonline,
the mailed Microfilm Order Form, or 866-272-6272; the price may be stale). You need the publication number (M1118) and
the roll numbers, which the roll list from item 1 supplies. Roll 13 holds 1932; the 1862–1925 orders sit on lower
rolls, number unknown until the list arrives. Estimated cost: 12 rolls × $125 = $1,500 if the pre-1925 orders fill
twelve rolls; the list decides. Drop the delivered images in `research/owner-inbox/m1118/<roll>/`; the session hashes,
splits and aligns them and registers each order as a public-domain `microfilm_witness`, which then replaces every
Hein-dependent and ProQuest-dependent witness.

## 3. HathiTrust login downloads (never fetched by automation; ruling R40)

Download with your HathiTrust member login and drop in `research/owner-inbox/hathi-gpo/` (git-ignored):

| Handle | What it unlocks |
|---|---|
| `uc1.31822012294732` | *Executive orders relating to Indian reservations 1855–1922*, vol. 2: full printings of the 1912–1922 reservation orders (46 frame orders by WPA subject) |
| record 001719532 (31 vols) | *Civil Service Act and Rules* pamphlets: the "CSA" citations the WPA list gives for 139 orders, which the Serial Set does not cover |
| record 000065622 | War Department *General Orders* 1905–1918: military-reservation orders reprinted in full |
| `coo.31924103151951` | CSC annual report FY1904: the one report year the Serial Set set lacks (3 unresolved WPA citations; the Google-scanned IA copies turned out to be FY1915, FY1918 and FY1922) |
| `mdp.39015049033908` | Alien Property Custodian report 1919: the 1917–1919 APC orders |
| `hvd.hl272j` onward | the GPO bound volumes for 7316–8314 are already downloaded; the series continues on record 000070271 |

## 4. HeinOnline checklist (lane 7; by hand only)

`research/photius/HEIN_OWNER.md` carries the User Rules text and the block list; `research/photius/HEIN_BLOCKS.csv`
has one row per residual order with volume, block, page id and URL. Standing rule: view and record, or save a block
PDF one at a time by its PDF icon, in your own browser; never script, never bulk; nothing from Hein goes in the public
repository. Drop saved PDFs in `research/owner-inbox/hein/<volume>-<block>.pdf`, or record page facts in
`research/owner-inbox/hein-checks.csv` (number, date, signatory, first_words, last_words, page_id).

## 5. Drop locations (all git-ignored under `research/owner-inbox/`)

| Folder | Holds |
|---|---|
| `hathi-gpo/` | Google-digitized HathiTrust PDFs (twelve already there, with `MANIFEST.json` and `SHA256SUMS.txt`) |
| `hein/` | HeinOnline block PDFs, named `<volume>-<block>.pdf` |
| `hein-checks.csv` | page facts recorded from Hein by hand |
| `m1118/<roll>/` | NARA digitized roll images |
| `nara/` | NARA correspondence |

Only hashes, page references and extracted text leave these folders.
