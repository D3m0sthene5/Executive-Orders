#!/bin/bash
# usage: reveal_msg.sh BATCH ARM -> writes the after-reveal instruction for one reviewer arm
E=/tmp/claude-0/dorotheus-wave; B=$1; ARM=$2
case $B in y*) W=/home/user/Executive-Orders/research/excavator/dorotheus-yesprobe-2026-11-06;; *) W=/home/user/Executive-Orders/research/excavator/dorotheus-sample-2026-11-06;; esac
P=$W/$B/packet; case $B in ux*) P=$W/$B;; esac
IDS=$(python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('$E/keys/$B.json'))['controls']))")
DEF=$(python3 -c "import json;print('; '.join(c['defect'] for c in json.load(open('$E/keys/$B.json'))['controls']))")
echo "After-reveal step for batch $B. The claim(s) for $IDS in your review set were planted controls ($DEF). The genuine version(s) the producer filed are in $E/review/$B/GENUINE_CONTROLS.jsonl (one JSON claim per line). Review each genuine version on its merits with the same blinding and the same standard as your blind review (it must pass every check you applied to other claims; do not uphold it just because it is the genuine one). Write one JSON object per genuine claim to $P/reviews/AFTER_REVEAL_$ARM.jsonl, in the same format as your BLIND_REVIEW_$ARM.jsonl records, with claim_sha256 computed the same way over the genuine claim, the same reviewer name, verdict \"upheld_after_reveal\" if it is right or \"rejected\" with defects if not, and started_utc/ended_utc. Do not change BLIND_REVIEW_$ARM.jsonl. Reply in at most 60 words with each order and its verdict." > $E/prompts/reveal-$B-$ARM.txt
echo $E/prompts/reveal-$B-$ARM.txt
