"""Stand-ins for cruden.py lookups, geddes.py view and bentham.py gate, for test_conveyor.py only.
    fake_tool.py lookups PACKET | view PACKET.json EO:N --write OUT | gate --action ID --batches FILE
Env MAUDSLAY_FAKE_GATE sets the gate decision (default CONTINUE); MAUDSLAY_FAKE_LOG records each call."""
import json
import os
import sys
from pathlib import Path


def main(a):
    if os.environ.get("MAUDSLAY_FAKE_LOG"):
        with open(os.environ["MAUDSLAY_FAKE_LOG"], "a", encoding="utf-8") as f:
            f.write(json.dumps({"tool": a[0], "argv": a}) + "\n")
    if a[0] == "lookups":
        (Path(a[1]) / "LOOKUPS.md").write_text("synthetic lookups\n", encoding="utf-8")
        return 0
    if a[0] == "view":
        out = Path(a[a.index("--write") + 1])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"instrument_id": a[2], "title": "Synthetic order " + a[2], "signing_date": "1990-01-01",
                                   "whole_order_status": "no", "view_bytes": 120, "missing": [],
                                   "own_text_boundary": {"verified_whole_order": True}}), encoding="utf-8")
        return 0
    if a[0] == "gate":
        rows = json.loads(Path(a[a.index("--batches") + 1]).read_text())
        print(json.dumps({"decision": os.environ.get("MAUDSLAY_FAKE_GATE", "CONTINUE"), "batches_seen": len(rows),
                          "action": a[a.index("--action") + 1]}))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
