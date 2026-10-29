"""Write a batch's source-supplement declaration for the shared NIRA excerpts.

Usage: python3 research/excavator/claude-nira-sweep-2026-10-29/make_declarations.py PACKET_DIR OUT.json

Every decided member of the parent packet receives the same seven excerpts from SUPPLEMENT_SOURCES.json
(S.J. Res. 113; NIRA sections 2(c), 3 and 5; three Schechter passages). The excerpt spans and hashes are
rechecked against the held files. The declaration is ordinary input for jobs/claim-kit/source_supplement.py;
it states no finding, date or legal application for any order.
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main(packet_dir, out):
    spec = json.loads((HERE / "SUPPLEMENT_SOURCES.json").read_text(encoding="utf-8"))
    packet = json.loads((Path(packet_dir) / "PACKET.json").read_text(encoding="utf-8"))
    members = sorted(packet["dossiers"])
    if not members:
        raise SystemExit("no members found in PACKET.json")
    sources = []
    for s in spec["sources"]:
        src = s["source"]
        for key, path in (("sha256", "local_path"), ("text_sha256", "text_path")):
            if hashlib.sha256((REPO / src[path]).read_bytes()).hexdigest() != src[key]:
                raise SystemExit("held file changed: " + src[path])
        text = (REPO / src["text_path"]).read_bytes().decode("utf-8")
        if hashlib.sha256(text[s["char_start"]:s["char_end"]].encode()).hexdigest() != s["excerpt_sha256"]:
            raise SystemExit("excerpt span changed: " + s["alias"])
        sources.append({"alias": s["alias"], "instrument_ids": members, "actor_id": s["actor_label"],
                        "reason": s["reason"], "char_start": s["char_start"], "char_end": s["char_end"],
                        "source": src})
    Path(out).write_text(json.dumps({"schema": "eo-source-excerpt-declarations/v1", "sources": sources},
                                    indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{len(sources)} excerpts x {len(members)} members -> {out}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
