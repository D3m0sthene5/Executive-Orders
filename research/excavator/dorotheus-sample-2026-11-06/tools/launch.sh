#!/bin/bash
# usage: launch.sh NAME MODEL PROMPTFILE -> one fresh headless Claude Code worker (separate context);
# result JSON in /tmp/claude-0/dorotheus-wave/run/NAME.json; start/end/cost/turns appended to COORDINATOR_LOG.txt
E=/tmp/claude-0/dorotheus-wave; N=$1; M=$2; P=$3
cd $E/run
echo "LAUNCH $N model=$M start=$(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
claude -p --model $M --output-format json --permission-mode auto --allowedTools "Bash Read Write Edit Grep Glob" --add-dir /home/user/Executive-Orders < $P > $E/run/$N.json 2> $E/run/$N.err
python3 -c "import json;d=json.load(open('$E/run/$N.json'));u=d.get('usage',{});print('END $N model=$2 session='+str(d.get('session_id')), 'cost='+str(d.get('total_cost_usd')), 'turns='+str(d.get('num_turns')), 'in='+str(u.get('input_tokens')), 'cache_read='+str(u.get('cache_read_input_tokens')), 'cache_write='+str(u.get('cache_creation_input_tokens')), 'out='+str(u.get('output_tokens')), 'subtype='+str(d.get('subtype')))" >> $E/COORDINATOR_LOG.txt 2>&1 || echo "END $N FAILED_TO_PARSE" >> $E/COORDINATOR_LOG.txt
echo "DONE $N end=$(date -u +%FT%TZ)" >> $E/COORDINATOR_LOG.txt
