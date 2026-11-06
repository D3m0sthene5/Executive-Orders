"""render.py TEMPLATE WORKER BATCH [ASSIGNED...] -> scratch prompts/WORKER.txt (coordinator tool)."""
import sys
S='/tmp/claude-0/-home-claude/1b28d9a2-1935-5c00-acfa-76feacb7b775/scratchpad/herschel-H3/prompts/'
tpl, w, b = sys.argv[1:4]; assigned = sys.argv[4:]
P='/home/claude/executive-orders/research/herschel/H3/packets/'+b
t=open('/home/claude/executive-orders/research/herschel/H3/tools/prompts/'+tpl).read()
t=t.replace('PACKETPATH',P).replace('<PACKET>',P).replace('WORKER',w)
if assigned:
    t=t.replace('ASSIGNED MEMBERS: every member of your packet.', 'ASSIGNED MEMBERS: '+', '.join(assigned)+'. Rows for any other member of the packet are already filled as `blocked` by the coordinator (they failed the pre-assignment dispatch check on source custody); do not change those rows and do not research those orders.')
open(S+w+'.txt','w').write(t); print(S+w+'.txt')
