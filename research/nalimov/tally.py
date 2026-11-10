"""Nalimov reach tally: why each candidate order is not scriptable, and what would remove the reason. Zero tokens.

Reads research/nalimov/census/CENSUS.csv (every express candidate on the undecided route and every decided NO order
without a ready claim). Each blocker is mapped to the remedy that removes it:
  F3, F4, F6, F7  Accursius claim-kit fixes (#272, #275, #276, #273); F5 (#274) opens only the amendment-only kind
  sources         an acquisition (official copies, page images, files missing from the data checkout; Linnaeus)
  tier:<name>     a new Nalimov drafter tier: a script reading that the current drafter refuses by design
  kind:<name>     a different kind of order (another Respondendi lot), not this drafter
Some blockers need two remedies (a fix makes text held, a tier must then read it); they are mapped to both, and an
order is counted as unlocked at a level only if every one of its blockers is removed at that level.

    python -I research/nalimov/tally.py > research/nalimov/TALLY.json
"""
import collections
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
csv.field_size_limit(1 << 30)

# blocker name -> remedies (all needed)
REMEDY = {
    # inventory and page spans: F7
    "inventory_gap": ["F7"], "clause_spans_several_sections": ["F7"], "clause_starts_in_file_header": ["F7"],
    "order_number_line_outside_inventory": ["F7"], "no_clause_inventory": ["F7"], "clause_text_missing": ["F7"],
    # acting texts routed into the dossier: F4 makes the text held; a tier must then read whether it acts
    "actor_text_not_held": ["F4"], "conflict_actor_text_not_held_or_too_long": ["F4"],
    "missing_item:target provision not located": ["F4", "tier:read_unlocated_actor"],
    "missing_item:No compiled selected actor text located": ["F4"],
    "missing_item:Acting identity absent from census": ["F4", "tier:non_census_actor"],
    "missing_item:Large actor context must be read at": ["F4"],
    "missing_item:cited by number, no change provision located": ["F4", "tier:read_unlocated_actor"],
    "missing_item:names the same person": ["tier:read_unlocated_actor"],
    "missing_item:Machine segmentation lead": ["F7"],
    "missing_item:Official-source page location requires a separate page/image check": ["sources"],
    "missing_item:Provisional working text requires": ["F6"],
    "missing_item:Held representation is a lead": ["sources"],
    "missing_item:No dated status observation or later event was located": ["tier:empty_history"],
    # current law: F3 makes notes and sections held text; a tier must read them
    "current_law_lead_needs_reading": ["F3", "tier:read_current_law"],
    "current_law_mention_needs_reading": ["F3", "tier:read_current_law"],
    "usc_note_says_this_order_amended_another": ["tier:amending_order"],
    # text gates
    "original_not_acceptable": ["F6"],
    "page_check_owed": ["sources"], "target_signing_date_missing": ["sources"], "freeze_refused": ["sources"],
    "ending_source_is_working_text": ["sources"],
    # judgments a later tier could script
    "another_instrument_acts": ["tier:recorded_amendments"], "chain_event_by_another_actor": ["tier:recorded_amendments"],
    "same_actor_other_act": ["tier:recorded_amendments"], "catalog_entry_acts_on_order": ["tier:recorded_amendments"],
    "same_actor_partial_act": ["tier:partial_ends"], "several_ending_actors": ["tier:first_of_several_ends"],
    "own_term_needs_reading": ["tier:own_terms_before_end"],
    "effective_wording_unparsed": ["tier:delayed_effect"], "actor_effective_sentence_needs_reading": ["tier:delayed_effect"],
    "effective_class_needs_reading": ["tier:delayed_effect"], "end_date_not_derivable": ["tier:delayed_effect"],
    "dates_out_of_order": ["tier:delayed_effect"],
    "actor_savings_sentence": ["tier:savings"], "savings_phrase_in_provision": ["tier:savings"],
    "clause_needs_judgment": ["tier:one_time_commands"], "no_continuing_command": ["kind:spent_on_issue"],
    "no_second_witness": ["tier:second_witness"], "witness_date_differs": ["tier:second_witness"],
    "history_flag_needs_reading": ["tier:history_flags"], "dossier_conflict_needs_reading": ["tier:history_flags"],
    "conflict_actor_prints_the_number": ["tier:history_flags"],
    "reinstatement_or_continuation_lead": ["tier:recorded_amendments"], "catalog_reinstatement": ["tier:recorded_amendments"],
    "decided_status_not_no": ["kind:yes_current"],
}
# decided orders with no predicate-passing ACT: the kind their held evidence points to
NO_ACT = {"own_terms_only": ["kind:own_terms"], "partial_acts_only": ["tier:partial_ends"],
          "whole_named_act_failing_sentence_test": ["tier:qualified_or_odd_wording"],
          "acts_not_naming_or_not_whole": ["tier:read_unlocated_actor"],
          "chain_events_without_located_provision": ["F4", "tier:read_unlocated_actor"],
          "no_later_instrument_or_term_held": ["sources", "kind:not_scriptable_from_held_evidence"]}
LEVELS = [("F3-F7 alone", lambda r: r in {"F3", "F4", "F5", "F6", "F7"}),
          ("F3-F7 + sources", lambda r: r in {"F3", "F4", "F5", "F6", "F7", "sources"}),
          ("F3-F7 + sources + new drafter tiers", lambda r: not r.startswith("kind:")),
          ("everything, including other kinds", lambda r: True)]


def remedies(row):
    out = []
    for b in [x for x in row["blockers"].split(" | ") if x]:
        name = b.split(":")[0]
        if name == "missing_item":
            text = b.split(":", 1)[1].strip()
            key = next((k for k in REMEDY if k.startswith("missing_item:") and text.startswith(k.split(":", 1)[1])), None)
            out.append((key or "missing_item:other", REMEDY.get(key, ["tier:other_missing_item"])))
        elif name == "no_express_named_whole_revocation":
            ev = row.get("ending_evidence") or "no_later_instrument_or_term_held"
            out.append((f"no_express_act:{ev}", NO_ACT.get(ev, ["kind:other"])))
        else:
            out.append((name, REMEDY.get(name, ["tier:unmapped:" + name])))
    return out


def main():
    rows = [r for r in csv.DictReader(open(HERE / "census/CENSUS.csv", encoding="utf-8"))
            if r["kind"] in ("express_named_revocation", "decided_express")]
    result = {"schema": "nalimov-tally/v1", "basis": "research/nalimov/census/CENSUS.csv (origin/main 854514831e outputs)",
              "note": "Counts are upper bounds on what a remedy unlocks: an order counts as unlocked at a level only if "
                      "every blocker it has is removed at that level, and a fix is assumed to remove its blockers for "
                      "every order it touches. The real number needs a census rerun after each fix merges.",
              "populations": {}}
    for kind in ("express_named_revocation", "decided_express"):
        mine = [r for r in rows if r["kind"] == kind]
        blocked = [r for r in mine if r["complete"] != "True"]
        by_blocker, by_remedy, first = collections.Counter(), collections.Counter(), collections.Counter()
        unlocked = collections.Counter()
        for r in blocked:
            rs = remedies(r)
            first[rs[0][0]] += 1
            for name in {n for n, _ in rs}:
                by_blocker[name] += 1
            for rem in {x for _, need in rs for x in need}:
                by_remedy[rem] += 1
            needed = {x for _, need in rs for x in need}
            for label, ok in LEVELS:
                if all(ok(x) for x in needed):
                    unlocked[label] += 1
        complete = len(mine) - len(blocked)
        result["populations"][kind] = {
            "orders": len(mine), "complete_now": complete, "blocked": len(blocked),
            "orders_with_blocker": dict(by_blocker.most_common()),
            "orders_needing_remedy": dict(by_remedy.most_common()),
            "first_blocker": dict(first.most_common()),
            "scriptable_if": {label: complete + unlocked[label] for label, _ in LEVELS}}
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
