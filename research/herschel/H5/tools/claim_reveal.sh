#!/bin/bash
# usage: claim_reveal.sh BATCH WA WB -> tells both blind reviewers which claims were planted and asks for an
# after-reveal review of each genuine control (reviews/AFTER_REVEAL_<ARM>.jsonl). Coordinator tool.
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H5
R=/home/claude/executive-orders; B=$1; P=$R/research/herschel/H5/packets/$B/packet
IDS=$(python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('$E/keys/$B.json'))['controls']))" 2>/dev/null || python3 -c "import json;print(', '.join(c['instrument_id'] for c in json.load(open('$E/moon-keys/$B.json'))['controls']))")
for arm in A B; do W=$2; [ $arm = B ] && W=$3
cat > $E/prompts/$W-reveal.txt <<EOM
Reveal: in your set the claim(s) for $IDS were planted controls (every first_end and whole_order_end date moved back exactly three years). The genuine version(s) are in $E/moon-review/$B/GENUINE_CONTROLS.jsonl (you may now open that one file). Review each genuine claim on its merits exactly as before (hash and quote checks, ending source, earlier-end test, savings) and write one JSON line per claim to $P/reviews/AFTER_REVEAL_$arm.jsonl in the same format as your blind review, with "after_reveal": true, verdict "upheld_after_reveal" or "rejected", and claim_sha256 of the genuine claim. Change nothing else. Reply in at most 60 words.
EOM
(nohup bash $R/research/herschel/H5/tools/reveal.sh $W $E/prompts/$W-reveal.txt > /dev/null 2>&1 &)
done
