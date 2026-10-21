set -e
cd /home/user/Executive-Orders
B=/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/lambertini2/b2
D=research/excavator/lambertini-2026-10-20/scale/02
python3 $B/build.py
rm -f $D/claims_assembled.jsonl $D/claims_assembled.report.json
python3 jobs/claim-kit/kit.py assemble $D/sheets --write $D/claims_assembled.jsonl
python3 $B/splice.py
python3 jobs/claim-kit/kit.py check $B/claims_spliced.jsonl | python3 -c "
import sys,json
t=sys.stdin.read(); d=json.loads(t[t.index('['):]) if '[' in t else None
print('kit.check errors per line:', [ (x['line'],x['errors']) for x in d] if d else t[:500])"
rm -rf $B/chk_out $B/chk_cache; mkdir -p $B/chk_out $B/chk_cache
REPO_ROOT=. OUTPUT_DIR=$B/chk_out JOB_CACHE_DIR=$B/chk_cache CLAIM_CHECKER_CLAIMS=$B/claims_spliced.jsonl python3 jobs/claim-checker/job.py > $B/chk.log 2>&1
tail -6 $B/chk.log
