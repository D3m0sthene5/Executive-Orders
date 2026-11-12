"""Offline population contract and post-build coverage checks.

The contract records already accepted inputs; neither a changed progress CSV nor
an unmerged review file authorizes an addition. Updating the contract requires
the existing owner-adoption process. Historical fixtures remain frozen.

Run input validation before building. Check derived coverage *after* preparing
outputs, so a stale generation cannot prevent its own replacement.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import re


HERE = Path(__file__).resolve().parent
CONTRACT = HERE / "population_contract.json"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(value):
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False).encode("utf-8"))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_csv(data):
    return list(csv.DictReader(io.StringIO(data.decode("utf-8-sig"), newline="")))


def repo_file(repo, relative):
    path = (repo / relative).resolve()
    require(path.is_relative_to(repo.resolve()), "Population path escapes repository")
    return path


def unique_rows(rows, key, label):
    result = {}
    for row in rows:
        iid = row.get(key)
        require(isinstance(iid, str) and bool(iid), label + ": missing identity")
        require(iid not in result, label + ": duplicate identity " + iid)
        result[iid] = row
    return result


def pinned_bytes(repo, pin):
    data = repo_file(repo, pin["path"]).read_bytes()
    require(sha(data) == pin["sha256"], "Population authorization pin changed: " + pin["path"])
    return data


def validate_inputs(repo, contract=None):
    """Validate exact census identities and accepted rows, never infer adoption."""
    repo = Path(repo).resolve()
    contract = contract or json.loads(CONTRACT.read_text(encoding="utf-8"))
    require(contract.get("schema") == "eo-accepted-population-contract/v1", "Population contract schema")
    census = contract["census"]
    census_rows = read_csv(repo_file(repo, census["path"]).read_bytes())
    identities = unique_rows(
        [{"instrument_id": row.get("id") or row.get("instrument_id")} for row in census_rows
         if row.get("included_in_bibliography", "1") == "1"], "instrument_id", "Census")
    # Owner ruling R9 (2026-11-06): the census may exceed the frozen 14,972 by pinned admissions and may
    # spell a renamed id differently (EO:7933a -> EO:7933A). The count/hash pin is checked on the original
    # population: admitted ids removed, renamed ids mapped back to their historical spelling.
    aliases = dict(census.get("id_aliases", {}))            # historical id -> current census id
    admitted_ids = set()
    admissions = census.get("admissions") or []
    if isinstance(admissions, dict):   # R9 (one file); D-20261112-graunt-apply made it a list of pinned files
        admissions = [admissions]
    for entry in admissions:
        ids_here = {(row.get("id") or row.get("instrument_id")) for row in read_csv(pinned_bytes(repo, entry))}
        require(len(ids_here) == entry["count"], "Census admissions count changed")
        require(ids_here <= set(identities), "Pinned admission absent from census")
        require(not (ids_here & admitted_ids), "Census admission listed twice")
        admitted_ids |= ids_here
    back = {new: old for old, new in aliases.items()}
    original = [back.get(i, i) for i in identities if i not in admitted_ids]
    require(len(original) == census["count"], "Census identity count changed")
    require(canonical_sha(sorted(original)) == census["identity_sha256"], "Census identities changed")

    baseline = contract["historical_status_baseline"]
    current = repo_file(repo, baseline["path"]).read_bytes()
    frozen = current[:baseline["bytes"]]
    require(sha(frozen) == baseline["sha256"], "Frozen historical status bytes changed")
    expected = read_csv(frozen)
    require(len(expected) == baseline["count"], "Historical status fixture count changed")
    require(canonical_sha(expected) == baseline["rows_sha256"], "Historical status fixture rows changed")
    for adoption in contract["accepted_additions"]:
        # These independent, pinned acceptance records are not discovered from
        # the mutable ledger. Preserve the owner ruling and review provenance.
        require(bool(adoption.get("accepted_in_main")), "Unaccepted population addition")
        for pin in adoption["authorization_pins"]:
            pinned_bytes(repo, pin)
        rows = read_csv(pinned_bytes(repo, adoption["rows"]))
        require(len(rows) == adoption["count"], "Accepted addition count changed")
        require(all(row.get("provisional_substantive_status") in {"yes", "no"}
                    and row.get("human_certified_by_this_release") == "no"
                    for row in rows), "Accepted addition exceeds provisional scope")
        expected.extend(rows)
    approved = unique_rows(expected, "instrument_id", "Accepted population")
    actual = read_csv(current)
    unique_rows(actual, "instrument_id", "Current population")
    require(actual == expected, "Current status rows differ from independently pinned accepted inputs")
    require({aliases.get(i, i) for i in approved} <= set(identities), "Accepted status identity absent from census")
    statuses = {aliases.get(iid, iid): row["provisional_substantive_status"] for iid, row in approved.items()}
    require(all(value in {"yes", "no"} for value in statuses.values()), "Unsupported provisional status")
    return {
        "schema": "eo-validated-population/v1",
        "contract_sha256": canonical_sha(contract),
        "historical_decided": baseline["count"],
        "authorized_additions": sum(a["count"] for a in contract["accepted_additions"]),
        "universe": len(identities), "decided": len(statuses),
        "identity_sha256": canonical_sha(sorted(identities)),
        "status_sha256": canonical_sha(statuses), "statuses": statuses,
        "id_aliases": aliases,
    }


def check_membership(rows, statuses, status_key, label):
    records = unique_rows(rows, "instrument_id", label)
    require(set(records) == set(statuses),
            label + " coverage stale: missing=" + str(sorted(set(statuses) - set(records))) +
            "; extra=" + str(sorted(set(records) - set(statuses))))
    require(all(row.get(status_key) == statuses[iid] for iid, row in records.items()),
            label + " statuses stale")
    return records


def validate_derived(population, drafts=None, dossiers=None):
    """Require exact membership/statuses, not a count-only SUMMARY agreement."""
    statuses = population["statuses"]
    report = {"decided": len(statuses), "drafts": None, "dossiers": None}
    if drafts is not None:
        drafts = Path(drafts)
        summary = json.loads((drafts / "SUMMARY.json").read_text(encoding="utf-8"))
        require(summary.get("scope") in {"decided", "all"} and summary.get("job_limit") is None,
                "Draft output is not the complete decided population")
        require(summary.get("decided_orders_with_draft") == len(statuses), "Draft summary population stale")
        # claim-drafts.RollingWriter uses _2, _3, ... (claim-kit instead uses
        # .partNNNN). Do not accidentally include DRAFT_CLAIMS_UNDECIDED shards.
        paths = [drafts / "DRAFT_CLAIMS.jsonl"] + sorted(
            path for path in drafts.glob("DRAFT_CLAIMS_*.jsonl")
            if re.fullmatch(r"DRAFT_CLAIMS_[2-9][0-9]*\.jsonl|DRAFT_CLAIMS_1[0-9]+\.jsonl", path.name))
        def records():
            for path in paths:
                with path.open(encoding="utf-8") as fh:
                    for line in fh:
                        if line.strip():
                            record = json.loads(line)
                            iid = record.get("instrument_id")
                            # Owner ruling R9: drafts may still carry a historical id spelling.
                            yield {"instrument_id": population.get("id_aliases", {}).get(iid, iid),
                                   "status": record.get("_draft", {}).get("provisional_status")}
        check_membership(records(), statuses, "status", "Draft")
        report["drafts"] = "exact coverage and statuses passed"
    if dossiers is not None:
        dossiers = Path(dossiers).resolve()
        summary = json.loads((dossiers / "SUMMARY.json").read_text(encoding="utf-8"))
        counts = summary["counts"]
        require(counts.get("decided_orders") == counts.get("dossiers") == len(statuses),
                "Dossier summary population stale")
        require(counts.get("universe_orders") == population["universe"], "Dossier census stale")
        index = json.loads((dossiers / "INDEX.json").read_text(encoding="utf-8"))
        records = check_membership(index, statuses, "status", "Dossier index")
        files = set()
        for iid, entry in records.items():
            path = repo_file(dossiers, entry["dossier"])
            require(path.parent == dossiers / "dossiers", "Dossier path outside dossiers directory")
            require(path not in files, "Dossier file reused for different identities")
            files.add(path)
            dossier = json.loads(path.read_text(encoding="utf-8"))
            require(dossier.get("instrument_id") == iid and
                    dossier.get("whole_order_status") == statuses[iid], "Dossier identity/status stale: " + iid)
            fingerprint = canonical_sha({key: value for key, value in dossier.items() if key != "fingerprint"})
            require(dossier.get("fingerprint") == entry.get("fingerprint") == fingerprint,
                    "Dossier index/content fingerprint stale: " + iid)
        require(files == set((dossiers / "dossiers").glob("*.json")), "Dossier file coverage stale")
        report["dossiers"] = "exact index/file coverage and statuses passed"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=HERE.parents[1])
    parser.add_argument("--drafts", type=Path)
    parser.add_argument("--dossiers", type=Path)
    args = parser.parse_args()
    population = validate_inputs(args.repo)
    result = {k: value for k, value in population.items() if k != "statuses"}
    result["derived"] = validate_derived(population, args.drafts, args.dossiers)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
