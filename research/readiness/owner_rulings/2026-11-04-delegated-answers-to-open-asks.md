# Owner decision: answers to the eleven open owner questions (2026-11-04)

On 2026-11-03 at 23:34 EST the owner, Danny, told Claude in chat to "answer all open asks reasonably". Claude
answered each open Kean question below under that delegation. Each answer is the owner's decision because he
delegated it, but Claude chose the wording, so the owner may reverse any of them. Where an answer needs an action only
the owner can take (a letter, an account key, a setting outside the repository), the action is listed and remains his.

## Answers

**A-20261018-1. Send the drafted archival reference and scan requests?** Yes. Pre-1862 orders have no other route
to an original. The owner sends them from his own email or the NYU library account, starting with the National
Archives letters-received series in `research/plans/SCAN_REQUESTS_2026-10-18.md`, because the requests need a
named requester and may involve fees. Agents do not send them.

**A-20261019-1. Risk-tiered review?** Run a trial, but do not adopt it yet. The 11,256 to 10,027 agent-hour saving
is a modelled assumption. A trial runs the lighter review and the full review on the same claims of one production
lot, with planted controls. The lighter review may be adopted for a risk tier only if it catches every planted
control in that tier and agrees with the full review on every verdict that changes whether a claim is filed. Until
then every claim gets the full blind review.

**A-20261021-1. Admit the June 1932 run EO 5853-5879?** Yes, as working identities, flagged as supported only by a
compiled source (the American Presidency Project dates and titles) until an original is located. They enter the
working bibliography and its counts, they are queued for Lewis to find originals, and they carry no authentication.
This follows the treatment of other orders held only as transcriptions. The census edit is a separate change made
by the census tooling, not by a production agent.

**A-20261021-2. Remove `LRS-10-21-Cold-Calls-Plain.pdf` from the public ProQuest folder?** Yes. It is class notes
uploaded by mistake. Removing the file from the current tree stops new copies; it remains in git history, and
purging history would rewrite every clone, so that is not done unless the owner asks for it.

**A-20261022-1. Add search keys as repository secrets?** Yes for `NARA_API_KEY` (the National Archives issues
catalog API keys on request at no charge) and `BRAVE_SEARCH_KEY` (Brave's API includes a small monthly credit, so
light use costs little or nothing). Hold `SERPAPI_KEY`, which is paid, until a Lewis run with the Brave key shows
how many orders general web search actually reaches. The owner creates the keys and adds them under
Settings > Secrets and variables > Actions; agents cannot create accounts or keys for him.

**A-20261028-1. Does the 2026-10-28 permission to merge every pull request stand?** Yes, with one limit. Agents may
merge their own pull requests once every required check passes and the work followed the review rules. A pull
request that changes the census, a provisional status, the codebook, an owner ruling, or any certified or
human-review count still waits for the owner.

**A-20261028-2. Make the Kean check a required status check for main?** Yes in principle, but only once it cannot
block the job runner. The runner commits results straight to main, and a classic required check would reject those
pushes. It is set up as a repository ruleset that applies to pull requests only, and it is switched on after a test
shows that runner commits still land.

**A-20261028-3. Add the Kean line to ChatGPT's custom instructions?** Yes. The owner pastes this line into ChatGPT
custom instructions: "For the Executive-Orders project, first read HANDOFF/KEAN.md in
D3m0sthene5/Executive-Orders and record results there before ending."

**A-20261029-1. Valla context change and package limit?** Approved, with conditions. A packet's Valla context
excludes its own package, and excludes a committed package only when that package shares no requested identity and
no shared rationale key with the packet. Anything that might be relevant still stales the packet. The per-query
limit rises from 100 to 400 packages and still fails closed above it. The change ships with tests for both rules. It
is made after the 2026-11-04 Tribonian production run is completed, because changing Valla while packets are in
flight would stale them.

**A-20261031-1. Keep the claims for EO 6471A and 7016, given the blinding slip?** Keep each one only if a fresh blind
reviewer upholds it. The slip exposed two lines of another batch's claim file, which cannot change the evidence but
weakens the independence of the review. A new reviewer, in a separate context and with a planted control, reviews
both claims. A claim it upholds stays filed with the second review recorded; a claim it rejects is superseded or
withdrawn.

**A-20261101-geddes-models. Sonnet or Opus for the Apollo retries?** Closed as moot. Claude ran the retries itself in
the 2026-11-02 Erasmus run.

No codebook, provisional status or evidence standard changes here. Certified: 0.
