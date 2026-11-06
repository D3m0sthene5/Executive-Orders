#!/bin/bash
# usage: render_producer.sh BATCH WORKER -> /home/claude/selden-scratch/prompts/WORKER.txt (coordinator tool)
cd /home/claude/executive-orders
B=$1; W=$2; R=research/selden/proof/packets/$B; P=/home/claude/executive-orders/$R/$(cat $R/PRODUCTION_PACKET)
IDS=$(python3 -c "import json;print(', '.join(json.load(open('$P/PACKET.json'))['dossiers']))")
mkdir -p /home/claude/selden-scratch/prompts /home/claude/selden-scratch/work/$W
sed -e "s#PACKETPATH#$P#g" -e "s#<PACKET>#$P#g" -e "s#WORKER#$W#g" -e "s#ASSIGNEDLIST#$IDS#" -e "s#REPLNOTE##" \
    -e "s#SELDENBRIEF#/home/claude/executive-orders/$R/SELDEN_BRIEF.md#g" research/selden/proof/tools/prompts/producer.txt \
    > /home/claude/selden-scratch/prompts/$W.txt
echo rendered $W
