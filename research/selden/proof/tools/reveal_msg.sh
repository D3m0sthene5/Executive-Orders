#!/bin/bash
# usage: reveal_msg.sh BATCH ARM -> prints the after-reveal message for one review arm (coordinator tool)
E=/home/claude/selden-scratch
B=$1; A=$2
P=/home/claude/executive-orders/research/selden/proof/packets/$B/${PK:-packet-s1}
IDS=$(python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('/root/selden-keys/$B.json'))['controls']))")
echo "After-reveal step for batch $B, arm $A. The claim(s) for $IDS in your review set were planted controls: every first_end and whole_order_end date was moved back three years. The genuine version(s) the producer filed are in /root/selden-keys/$B-GENUINE_CONTROLS.jsonl (one JSON claim per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must also pass every check you applied to other claims; do not uphold it just because it is the genuine one). Write one JSON object per genuine claim to $P/reviews/AFTER_REVEAL_$A.jsonl, in the same format as your BLIND_REVIEW_$A.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW_$A.jsonl. Reply in at most 60 words with each order and its verdict."
