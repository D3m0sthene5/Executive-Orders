#!/bin/bash
# usage: status_reveal.sh BATCH ARM -> writes the after-reveal message for one status review arm (coordinator tool)
S=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
B=$1; A=$2; P=/home/claude/executive-orders/research/herschel/H4/packets/$B/packet
python3 -I - "$S" "$B" "$A" "$P" <<'PY'
import json,sys,shutil
S,B,A,P=sys.argv[1:]
k=json.load(open(f'{S}/status-keys/{B}.json'))['controls']
ids=[c['order'] for c in k]
gdir=f'{S}/status-review/{B}-genuine'; import os; os.makedirs(gdir,exist_ok=True)
for c in k:
    n=c['order'].replace('EO:','EO_').replace(':','_')
    shutil.copy(f'{S}/status-keys/{B}-{n}.genuine.json', f'{gdir}/{n}.decision.json')
msg=(f"After-reveal step for status batch {B}, arm {A}. The decision(s) for {', '.join(ids)} in your set were planted controls: "
 "the recommended status was flipped and any proposed_intervals dates were moved back three years. The genuine producer decision(s) are in "
 f"{gdir}/ (EO_N.decision.json). Review each genuine version on its merits with the same blinding and standard as your blind review; do not accept it just because it is genuine. "
 f"Append one JSON object per genuine decision to {P}/reviews/AFTER_REVEAL_STATUS_{A}.jsonl in the same format as your blind records, with decision_sha256 over the genuine file's bytes and verdict \"accept_after_reveal\" or \"rejected\". "
 "Then, for EVERY decision you accepted (blind or after reveal), write the formal independent review record: run "
 f"`cd /home/claude/executive-orders && python3 jobs/claim-kit/kit.py overlay-review-sheet --evidence {P}/undecided/EO_N/EVIDENCE.json --decision {P}/undecided/EO_N/STATUS_DECISION.producer.json --reviewer claude-herschel-H4-status-reviewer-{B}-{A} --write {P}/reviews/STATUS_REVIEW_{A}_EO_N.json` "
 "(the genuine producer file; its sha256 must equal the decision_sha256 you accepted), then edit that JSON: independence_confirmed true, source_checks_confirmed true, decision \"accept\", checked_evidence_ids (the original plus every basis id you checked), and a substantive rationale stating exactly what you verified and what remains a lifecycle gap. "
 "Do not change BLIND_STATUS_REVIEW files or any producer file. Reply in at most 60 words with each order, verdict and the formal record paths.")
open(f'{S}/prompts/reveal-status-{B}-{A}.txt','w').write(msg); print(msg[:200])
PY
