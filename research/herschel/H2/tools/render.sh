#!/bin/bash
# usage: render.sh TEMPLATE WORKER "EO:a EO:b ..." [PACKETDIR] [BLOCKEDNOTE] -> scratch prompts/WORKER.txt
E=/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H2
T=/home/claude/executive-orders/research/herschel/H2/tools/prompts/$1.txt
python3 - "$T" "$2" "$3" "$4" "$5" > $E/prompts/$2.txt <<'PY'
import sys
t,w,o,p,b=sys.argv[1:6]
s=open(t).read()
for k,v in (("PACKETPATH",p),("<PACKET>",p),("PACKETDIR",p),("ASSIGNEDLIST",o),("ORDERLIST",o),("BLOCKEDLIST",b),("WORKER",w)):
    s=s.replace(k,v)
print(s)
PY
echo $E/prompts/$2.txt
