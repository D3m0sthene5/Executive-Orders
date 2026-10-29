"""Cost table from Claude Code session transcripts (existing harness telemetry; no model calls).

Usage: python3 costs.py LABEL=TRANSCRIPT.jsonl [LABEL=TRANSCRIPT.jsonl ...] [--since ISO] [--until ISO] > COSTS.json

For each transcript: model(s), API calls, uncached input, cache-write, cache-read and output tokens
(deduplicated by message id), first and last timestamps, tool calls by tool, and the characters of
tool results returned to the model, split by the command or tool that produced them. Tool-result
characters show which outputs fill the context; they are not tokens. The transcripts themselves stay
outside the repository; only this summary is committed.
"""
import collections
import json
import re
import sys


def kind(tool, inp):
    if tool != "Bash":
        return tool
    cmd = (inp or {}).get("command", "")
    m = re.search(r"kit\.py\s+(?:--\S+\s+\S+\s+)*(\w[\w-]*)", cmd)
    if m:
        return "kit.py " + m.group(1)
    for k in ("source_supplement.py", "claim-checker", "grep", "rg ", "python3", "sed", "cat", "ls", "find", "sha256sum", "date"):
        if k in cmd:
            return "bash:" + k.strip()
    return "bash:other"


def summarize(path, since=None, until=None):
    seen = set()
    usage = collections.Counter()
    models = collections.Counter()
    calls = 0
    tools = collections.Counter()
    result_chars = collections.Counter()
    pending = {}
    first = last = None
    for line in open(path, encoding="utf-8"):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        ts = d.get("timestamp")
        if ts and ((since and ts < since) or (until and ts > until)):
            continue
        msg = d.get("message") or {}
        if d.get("type") == "assistant":
            mid = msg.get("id")
            u = msg.get("usage") or {}
            if mid and mid not in seen and u:
                seen.add(mid)
                calls += 1
                models[msg.get("model")] += 1
                for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens"):
                    usage[k] += u.get(k) or 0
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    k = kind(block.get("name"), block.get("input"))
                    tools[k] += 1
                    pending[block.get("id")] = k
            if ts:
                first = first or ts
                last = ts
        elif d.get("type") == "user":
            content = msg.get("content")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        c = block.get("content")
                        n = len(c) if isinstance(c, str) else sum(len(x.get("text", "")) for x in c or [] if isinstance(x, dict))
                        result_chars[pending.get(block.get("tool_use_id"), "unknown")] += n
    total_in = usage["input_tokens"] + usage["cache_creation_input_tokens"] + usage["cache_read_input_tokens"]
    return {"models": dict(models), "api_calls": calls, "tokens": dict(usage),
            "total_input_tokens": total_in, "total_tokens": total_in + usage["output_tokens"],
            "first_utc": first, "last_utc": last, "tool_calls": dict(tools.most_common()),
            "tool_result_chars": dict(result_chars.most_common())}


def main(argv):
    since = until = None
    pairs = []
    i = 0
    while i < len(argv):
        if argv[i] == "--since":
            since = argv[i + 1]; i += 2; continue
        if argv[i] == "--until":
            until = argv[i + 1]; i += 2; continue
        pairs.append(argv[i].split("=", 1)); i += 1
    out = {"schema": "claude-transcript-costs/v1", "since": since, "until": until,
           "notice": "Harness transcript usage, deduplicated by message id. Cache reads are billed at a fraction of "
                     "uncached input; report them separately. Tool-result characters are not tokens.",
           "agents": {label: summarize(path, since, until) for label, path in pairs}}
    json.dump(out, sys.stdout, indent=1)
    print()


if __name__ == "__main__":
    main(sys.argv[1:])
