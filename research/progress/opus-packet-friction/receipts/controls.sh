set -e
S=/tmp/claude-0/-home-user-Executive-Orders/43dc4dbb-34dc-5dd9-8960-2e617340c49a/scratchpad/opus; cd $S
T=$S/replay/nra-pre; B=$T/research/excavator/claude-nira-sweep-2026-10-29/t6/packet/supp; C=$T/research/readiness/claims
clean(){ rm -f $C/claude-2026-10-29-nira-t5.jsonl $C/claude-2026-10-29-nira-t6.jsonl; }
# 1. repaired completion, competing publication of the SAME instruments mid-run (production t6 file)
clean
python3 replay_complete.py $T $B/completion/COMPLETION.json $B/replay-completionfix-sameid --inject research/readiness/claims/claude-2026-10-29-nira-t6.jsonl --publish --out results/t6_completionfix_sameid.json > results/t6_completionfix_sameid.log 2>&1 || true
# the injected copy occupies the target name: record whether anything else was written, then clean
ls -l $C | grep nira > results/t6_completionfix_sameid.claims.txt || true
clean
# 2. baseline completion, no concurrent publication
cd $T && git show HEAD:jobs/claim-kit/completion.py > /tmp/cbase && rm jobs/claim-kit/completion.py && cp /tmp/cbase jobs/claim-kit/completion.py && cd $S
python3 replay_complete.py $T $B/completion/COMPLETION.json $B/replay-base-norace --publish --out results/t6_base_norace.json > results/t6_base_norace.log 2>&1 || true
cmp $C/claude-2026-10-29-nira-t6.jsonl /home/user/Executive-Orders/research/readiness/claims/claude-2026-10-29-nira-t6.jsonl && echo BASE_NORACE_IDENTICAL > results/t6_base_norace.cmp
clean
echo finished
