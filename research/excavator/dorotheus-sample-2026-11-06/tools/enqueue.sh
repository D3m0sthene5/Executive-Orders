#!/bin/bash
# usage: enqueue.sh -> renders and queues attempt-1 producers for every prepared packet not yet queued
E=/tmp/claude-0/dorotheus-wave; T=$(dirname $(readlink -f $0))
for f in $E/prep-*.log; do b=$(basename $f .log); b=${b#prep-}
  grep -q "^DONE $b" $f || continue
  grep -q "^producer-$b-a1 " $E/queue.txt 2>/dev/null && continue
  grep -qx "producer-$b-a1" $E/scheduler.state 2>/dev/null && continue
  python3 -I $T/render_producer.py $b && echo "producer-$b-a1 sonnet $E/prompts/producer-$b.txt" >> $E/queue.txt
done
