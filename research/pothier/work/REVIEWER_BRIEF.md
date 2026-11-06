# Pothier doctrine reviewer brief (blind review)

You are an independent reviewer. You did not write the doctrine you are given and you must not try to find its
author's working files: read only the doctrine copy named in your assignment (a `.md` and a `.json` outside the
repository), the primary sources, the member texts and the project data listed below. Do not open
`research/pothier/doctrines/`, `research/pothier/work/*/NOTES.md`, any `FETCH_PROPOSED.jsonl`, or `/home/claude/pothier-sealed/`,
and do not use git. The repository is at `/home/claude/Executive-Orders` (read-only for you).

**The copy you review may contain deliberate errors** (for example a wrong statute citation, a wrong Statutes at
Large page, a wrong date, a wrong date rule, a mechanism that does not reach the members it is applied to). Other
errors may be genuine. Your job is to find every error, planted or genuine, by checking the doctrine against the
sources. Do not assume anything in the copy is right because it looks specific.

## What to check

1. **Every citation**: does the cited statute, order, regulation or case exist at that citation (volume, page,
   section, date, U.S. Code section)? Does it say what the doctrine says it says? For a source marked `held`, open the
   `held_path` file and confirm the `pin` phrase is there and supports the point. For a source not held, check it on
   the web (WebSearch/WebFetch: govinfo.gov, uscode.house.gov, ecfr.gov, law.cornell.edu, federalregister.gov,
   official agency sites) as far as you can and say what you could and could not verify.
2. **Every date and date rule**: effective dates, expiry periods, the rule each branch uses to date the lead.
3. **Every mechanism's reach**: does the later statute or instrument, by its terms, reach these members? The
   project's rule: a later general rule ends an order only if something shows it extinguished that order; a savings
   clause or a repeal of the *authority* is not an end; absence of a found revocation is not evidence either way; a
   `yes` lead needs a current-law predicate.
4. **The procedure on real members**: run `python3 -I jobs/pothier/pothier.py try <your copy>.json --hints`
   (the engine reads `jobs/pothier/output/MEMBERS.jsonl`), and read at least 10 member texts across the deciding
   branches (`primary_text_path` in MEMBERS.jsonl). Do branch conditions catch the orders they mean, and only those?
   Name members that a branch decides wrongly.
5. **Honesty of the undecided list**: are the `open` branches and the gaps stated truthfully?

## What to return

Write your review to the path in your assignment as JSON:

```json
{"doctrine_id": "...", "arm": "A or B", "reviewer_model": "...",
 "findings": [{"id": "R1", "location": "section/branch/source id", "claim": "what the doctrine says",
               "evidence": "what the source actually says, with citation or path", "severity": "error | unsupported | minor",
               "fix": "what it should say"}],
 "citations_checked": [{"source_id": "S1", "verdict": "verified | wrong | unverifiable", "note": "..."}],
 "members_checked": ["EO:..."], "wrong_member_decisions": [{"instrument_id": "...", "branch": "...", "why": "..."}],
 "verdict": "approve | approve_with_required_changes | reject", "summary": "plain sentences"}
```

Then reply with the verdict, the number of findings by severity, and the three most serious findings in one line each.
