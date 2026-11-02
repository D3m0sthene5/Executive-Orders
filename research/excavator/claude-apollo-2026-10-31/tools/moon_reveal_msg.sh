#!/bin/bash
# usage: moon_reveal_msg.sh BATCH -> prints the after-reveal message for that batch's blind reviewer
S=/tmp/claude-0/-home-claude/79a6cc5c-022c-506a-a289-86cc7ef89ecd/scratchpad
B=$1
if [[ $B == n* || $B == g01 || $B == g02 ]]; then P=/home/claude/executive-orders/research/excavator/claude-apollo-2026-10-31/$B/packet/supp; else P=/home/claude/executive-orders/research/excavator/claude-apollo-2026-10-31/$B/packet; fi
IDS=$(python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('$S/moon-keys/$B.json'))['controls']))")
cat <<MSG
After-reveal step for batch $B. The claim(s) for $IDS in your review set were planted controls: every first_end and whole_order_end date was moved back three years. The genuine version(s) the producer filed are in $S/moon-review/$B/GENUINE_CONTROLS.jsonl (one JSON claim per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must also pass every check you applied to other claims; do not uphold it just because it is the genuine one). Write one JSON object per genuine claim to $P/reviews/AFTER_REVEAL.jsonl, in the same format as your BLIND_REVIEW.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict "upheld_after_reveal" if it is right or "rejected" with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW.jsonl. Reply in at most 60 words with each order and its verdict.
MSG
