#!/bin/bash
# usage: reveal_msg.sh BATCH ARM -> after-reveal instruction for one reviewer arm (coordinator tool)
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2
B=$1; ARM=$2; O=/home/claude/executive-orders/research/herschel/H2/reviews/$B
python3 - $E/keys/$B.json $E/review/$B/GENUINE_CONTROLS.jsonl $O/AFTER_REVEAL_$ARM.jsonl $O/BLIND_REVIEW_$ARM.jsonl <<'PY'
import json,sys
k=json.load(open(sys.argv[1]))
ids=", ".join(c["instrument_id"] for c in k["controls"]); d="; ".join(c["defect"] for c in k["controls"])
print(f"After-reveal step. The item(s) for {ids} in your review set were planted controls ({d}). The genuine version(s) the producer wrote are in {sys.argv[2]} (one JSON object per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must pass every check you applied to the other items; do not uphold it because it is the genuine one). Write one JSON object per genuine item to {sys.argv[3]}, in the same format as your {sys.argv[4]} records, with the hash computed the same way over the genuine item, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. Do not change your blind review file. Reply in at most 60 words with each order and its verdict.")
PY
