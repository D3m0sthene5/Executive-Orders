#!/bin/bash
# usage: reveal_msg.sh BATCH ARM -> prints the after-reveal message for one review arm (coordinator tool)
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H4
B=$1; A=$2
P=/home/claude/executive-orders/research/herschel/H4/packets/$B/packet
IDS=$(python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('$E/moon-keys/$B.json'))['controls']))")
echo "After-reveal step for batch $B, arm $A. The claim(s) for $IDS in your review set were planted controls: every first_end and whole_order_end date was moved back three years. The genuine version(s) the producer filed are in $E/moon-review/$B/GENUINE_CONTROLS.jsonl (one JSON claim per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must also pass every check you applied to other claims; do not uphold it just because it is the genuine one). Write one JSON object per genuine claim to $P/reviews/AFTER_REVEAL_$A.jsonl, in the same format as your BLIND_REVIEW_$A.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW_$A.jsonl. Reply in at most 60 words with each order and its verdict."
