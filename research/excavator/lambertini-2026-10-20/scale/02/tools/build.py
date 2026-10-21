import json, sys, os, copy
sys.path.insert(0, os.path.dirname(__file__))
from spec import ORDERS, C

REPO = '/home/user/Executive-Orders'
S = '/tmp/claude-0/-home-user-Executive-Orders/dc388148-b92d-5956-9825-90ce34a3dac7/scratchpad/lambertini2/b2/'
OUT = REPO + '/research/excavator/lambertini-2026-10-20/scale/02/sheets/'
os.makedirs(OUT, exist_ok=True)
AGENT = 'claude-lambertini-s02-producer'
END_DATE = '2021-01-20'

TAIL = {
 'plain': "Ends with the whole order: EO 13990 sec. 7(a) revokes the order, effective on signing, 2021-01-20. The clause has no own-term end, sunset or termination-on-performance wording and no amendment to its text before 2021-01-20 is recorded in the held texts, so the revocation is its first end.",
 'deadline': "The time period in this clause is a report or action deadline, not an end: the order has no wording that terminates the clause when the report or action is done, and a performed command stays part of the order until it is revoked (AGENT_PROTOCOL step 3; BATCH.md). The producer does not claim the date any report was delivered; that date is not an end-date source. First end = EO 13990 sec. 7(a) revocation, effective on signing, 2021-01-20.",
 'emerg': "'For the duration of the national emergency' ties the recurring reports to the emergency declared by Proclamation 9994 (2020-03-13). No held text, U.S. Code note or OFR note records an end of that emergency before 2021-01-20 and it was still in force then, so the clause had no earlier own-term end. First end = EO 13990 sec. 7(a) revocation, effective on signing, 2021-01-20.",
 'revoke13754': "Sec. 4(c) was a completed, self-executing revocation of a different instrument. EO 13990 sec. 4(b) reinstated EO 13754 and the December 20, 2016 memorandum 'in their original form' on the same day, 2021-01-20 (86 FR 7039; the U.S. Code note to 15 U.S.C. 4101 says the same). The clause text ends with the order under EO 13990 sec. 7(a), effective on signing, 2021-01-20; the reinstatement is a separate provision of the same acting order and is handled under savings_residuals.",
 'memos': "Sec. 5 is a self-executing change to other Presidential instruments. EO 13990 sec. 4(b) reinstates only the December 20, 2016 memorandum; it does not mention the January 27, 2015 or July 14, 2008 memoranda. The text of sec. 5 ends with the order under EO 13990 sec. 7(a), effective on signing, 2021-01-20, but the modification it made outlives the revocation; that is recorded under savings_residuals (continuing_independent), not as a later end of this clause.",
}

def mech(n):
    o = ORDERS[n]
    return (f"express revocation by EO 13990 sec. 7(a) ('Executive Order {n} of {o['date']} ({o['title']}) ... [is] hereby revoked'); "
            "EO 13990 states no effective date and no delayed-effect wording, so the revocation took effect on signing, January 20, 2021 (printed 86 FR 7041-7042, January 25, 2021)")

EO13807_EVENT = {
 "id": "ACTOR_TEXT:EO:13807",
 "effective_date": "2017-08-15",
 "effective_date_confirmed": True,
 "mechanism": ("partial change, not an end: EO 13807 sec. 5(d) says that for implementing EO 13766 all infrastructure projects subject to 23 U.S.C. 139, "
               "33 U.S.C. 2348 or 42 U.S.C. 4370m-4370m-12 qualify as high priority, other classes may be added by the FPISC Executive Director, and the CEQ Chairman's "
               "responsibilities under sections 2 and 3 of EO 13766 'shall be satisfied by referring the project to the FPISC Executive Director, the Secretary of Transportation, "
               "or the Assistant Secretary of the Army for Civil Works'; it states no effective date, so effective on signing, August 15, 2017 (82 FR 40463, printed August 24, 2017). "
               "It did not revoke, suspend or end secs. 2-3, which continued until the revocation on 2021-01-20; EO 13807 was itself revoked by EO 13990 sec. 7(b) the same day"),
}
EXTRA_REASON = {
 ('13766', 'sec2'): " Later event: EO 13807 sec. 5(d) (2017-08-15) widened which projects qualify as 'high priority' and redirected the CEQ Chairman's sec. 2 responsibility to the FPISC Executive Director, the Secretary of Transportation or the Army Civil Works official; this changes who decides, it does not end the clause.",
 ('13766', 'sec3'): " Later event: EO 13807 sec. 5(d) (2017-08-15) redirected the CEQ Chairman's sec. 3 responsibility to the FPISC Executive Director, the Secretary of Transportation or the Army Civil Works official; this changes who acts, it does not end the clause.",
}
LATER = {('13766', 'sec2'): [EO13807_EVENT], ('13766', 'sec3'): [EO13807_EVENT]}

RATIONALE = {
 '13766': "EO 13766 (signed 2017-01-24, 82 FR 8657-8658), read in full from the held FR text, has the CEQ Chairman decide whether a project is 'high priority' (sec. 2) and set expedited deadlines (sec. 3), plus general provisions (sec. 4). It has no term, sunset or termination clause; the machine own-term hits are only 'implemented consistent with applicable law and subject to the availability of appropriations' (sec. 4(a)), a condition on performance, not an end. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it ('are hereby revoked') with no effective-date wording, so the revocation took effect on signing, 2021-01-20. The U.S. Code note to 42 U.S.C. 4370m says the same (revoked by EO 13990 sec. 7(a), 86 FR 7041); the note is corroboration only. Dossier lead 'target provision not located: EO:13807' resolved: EO 13807 (82 FR 40463, held FR text, read in full) does not revoke or amend the text of EO 13766; its sec. 5(d) implements EO 13766, widens the 'high priority' criteria and redirects the CEQ Chairman's secs. 2-3 responsibilities, so it is attached as a later event on secs. 2 and 3 (a partial change before the end). EO 13807 was revoked by EO 13990 sec. 7(b) the same day. A by-number scan of all 6,652 held FR-original texts finds EO 13766 named only in EO 13807 and EO 13990. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders in this batch and reinstate nothing, so no later instrument revives EO 13766. Inventory: the dossier's 10 clauses cover the operative text from the issuing words through sec. 4(d). Inventory correction: the dossier's lead clause 'I hereby direct as follows:' is only 27 characters, too short for the checker to verify, so inventory_overrides extend it backwards to the start of the issuing words ('By the authority vested in me as President ...'); all other spans are copied unchanged.",
 '13778': "EO 13778 (signed 2017-02-28, 82 FR 12497-12498), read in full from the held FR text, directs the EPA Administrator and the Assistant Secretary of the Army for Civil Works to review the 2015 'Waters of the United States' rule and propose rescinding or revising it (sec. 2), consider the Scalia definition of navigable waters (sec. 3) and carries general provisions (sec. 4). It has no term, sunset or termination clause; the machine own-term hits are only 'implemented consistent with applicable law and subject to the availability of appropriations' and the OMB non-impairment sentence, which are conditions, not ends. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it, effective on signing, 2021-01-20. Dossier lead 'target provision not located: EO:13790' resolved: EO 13790 (82 FR 20237, held FR text, read in full) sec. 4(c) only tells the new Interagency Task Force on Agriculture and Rural Prosperity to 'coordinate its efforts with other reviews of regulations or policy, including those conducted pursuant to' EO 13778; it does not revoke, amend, suspend or extend any provision of EO 13778, so it is ruled out and nothing is attached. A by-number scan of all 6,652 held FR-original texts finds EO 13778 named only in EO 13790 and EO 13990. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders and reinstate nothing. Inventory: the dossier's 10 clauses cover the operative text from sec. 1 through sec. 4(c); the unnumbered authority preamble is not a separate operative clause.",
 '13792': "EO 13792 (signed 2017-04-26, 82 FR 20429-20431), read in full from the held FR text, orders the Secretary of the Interior to review Antiquities Act monument designations made since 1996 (sec. 2(a)-(c)) and report to the President, an interim report within 45 days and a final report within 120 days (sec. 2(d)-(e)). The machine own-term kinds are report_deadline (sec. 2(d), 2(e)) and condition (sec. 3(b)). A report deadline is never an end; the order has no sunset or termination wording, so every clause remains part of the order until revoked. No clause's first end needs a report date, so the order is not blocked on the report-deadline question; the producer does not claim when either report was delivered. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it, effective on signing, 2021-01-20. The dossier lists no missing provision and no other actor provision; a by-number scan of all 6,652 held FR-original texts finds EO 13792 named only in EO 13990. The monument-boundary proclamations of 2017 were separate Presidential acts, not part of this order. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders and reinstate nothing. Inventory: the dossier's 18 clauses cover the operative text from sec. 1 through sec. 3(c); its scope labels for sec. 2(a)(v)-(vii) ('sec2-v', 'sec2-v-vi', 'sec2-v-vii') are irregular but each span is correct and no text is missing or duplicated.",
 '13795': "EO 13795 (signed 2017-04-28, 82 FR 20815-20818), read in full from the held FR text, sets an offshore energy strategy: lease-sale scheduling and seismic permitting (sec. 3), a sanctuary and marine-monument designation review with a 180-day report (sec. 4(a)-(b)), the revocation of EO 13754 (sec. 4(c)), a modification of three OCS withdrawal memoranda (sec. 5), several rule and guidance reviews (secs. 6-11) and general provisions. The only own-term hits are the implementation condition (sec. 13(b)) and the 60- and 180-day periods, which are deadlines, not ends. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it, effective on signing, 2021-01-20. EO 13990 sec. 4(b), the same day, reinstates EO 13754 and the December 20, 2016 memorandum 'in their original form' (86 FR 7039; the U.S. Code notes to 15 U.S.C. 4101 and 43 U.S.C. 1331 record the reinstatement and the revocation). No later amendment of EO 13795 before the revocation appears in the held FR texts (by-number scan of all 6,652 held FR-original texts: only EO 13990 names it), the OFR catalog edges or the U.S. Code notes. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders and reinstate nothing. Inventory: the dossier's 24 clauses cover the operative text from sec. 1 through sec. 13(c). Savings: the S0 prefill is overruled, see savings_residuals.",
 '13868': "EO 13868 (signed 2019-04-10, 84 FR 15495-15499), read in full from the held FR text, directs agency actions on energy infrastructure: Clean Water Act section 401 guidance and rules (sec. 3), LNG safety and rail-transport rules (sec. 4), a Labor Department review of ERISA data and proxy guidance (sec. 5), rights-of-way renewals (sec. 6), reports (secs. 7-9) and general provisions (sec. 10). The machine own-term kinds (condition, fixed_term, report_deadline, sunset_date) are all misleading: they pick up 60-, 100-, 120- and 180-day periods, '13 months' and '1 year' deadlines, and the word 'sunset' in sec. 6, which describes expiring rights-of-way grants issued by agencies, not an end of the order. None of these is an end and the order has no sunset or termination clause. No clause's first end needs a report date, so the order is not blocked on the report-deadline question. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it, effective on signing, 2021-01-20. The dossier lists no missing provision; a by-number scan of all 6,652 held FR-original texts finds EO 13868 named only in EO 13990. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders and reinstate nothing. Inventory correction: the dossier splits the tail of sec. 3(d) into a separate fragment clause 'sec3-c-dup2' and labels sec. 3(b)(i) and (ii) 'sec3-i-dup2' and 'sec3-i-ii-dup2'; inventory_overrides merge the fragment into sec3-d and rename the two spans sec3-b-i and sec3-b-ii. All other spans are copied unchanged, so 36 clauses cover the operative text from sec. 1 through sec. 10(c) with no gap or overlap.",
 '13927': "EO 13927 (signed 2020-06-04, 85 FR 35165-35170), read in full from the held FR text, directs agencies to speed infrastructure and recovery actions during the COVID-19 national emergency: transportation, Army civil works and Federal-lands projects (secs. 3-5), NEPA, ESA and Clean Water Act emergency procedures (secs. 6-8), other emergency authorities (sec. 9) and general provisions (sec. 10). Most operative sections set a 30-day report and then status reports 'at least every 30 days for the duration of the national emergency'. The machine own-term kinds (condition, emergency_duration, fixed_term, report_deadline) are not ends: 30-day periods are deadlines, and the emergency-duration wording would end the recurring reports only when the emergency ended, which was after 2021-01-20 (no held source records an earlier end). The order has no sunset or termination clause. No clause's first end needs a report date, so the order is not blocked on the report-deadline question. EO 13990 (86 FR 7037-7043, read in full; reading record scale/readings/LSP-EO_13990.json) sec. 7(a) revokes it, effective on signing, 2021-01-20; the U.S. Code note to 5 U.S.C. 601 says the same (86 FR 7041). The dossier lists no missing provision; a by-number scan of all 6,652 held FR-original texts finds EO 13927 named only in EO 13990. EO 14148 and EO 14154 (2025) revoke EO 13990 but name none of the six orders and reinstate nothing. Inventory correction: the dossier splits the tail of sec. 8(c) into a separate fragment clause 'sec8-a' ('(a)(i). Such status reports shall thereafter be provided...'); inventory_overrides merge it into sec8-c. All other spans are copied unchanged, so 44 clauses cover the operative text from sec. 1 through sec. 10(c) with no gap or overlap.",
}

SAVINGS = {
 '13766': ("none_after_bounded_search",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13766 with no savings, pending-matter or transition clause; sec. 8(a) is only a general non-impairment clause for statutory agency authority and saves no revoked order; sec. 7(f) tells the OMB Director and agency heads to rescind issuances that implement or enforce the revoked orders; nothing is transferred. Own-residual check, reading EO 13766 in full: it creates no right, benefit, property or fund (sec. 4(d) disclaims rights) and no continuing duty beyond directions to the CEQ Chairman and agencies; the 'high priority' designations and deadlines contemplated by secs. 2-3 are determinations made under the order, and EO 13807 sec. 5(d), which redirected the CEQ functions, was revoked the same day by EO 13990 sec. 7(b). S0 prefill (none_after_bounded_search) KEPT. Bounded search: EO 13766, EO 13807 and EO 13990 in full; a by-number scan of all held FR-original texts; the U.S. Code note to 42 U.S.C. 4370m (repeats the revocation)."),
 '13778': ("none_after_bounded_search",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13778 with no savings, pending-matter or transition clause; sec. 8(a) saves only statutory agency authority; sec. 7(f) tells the OMB Director and agency heads to rescind issuances implementing or enforcing the revoked orders; nothing is transferred. Own-residual check, reading EO 13778 in full: it directs a review and a proposed rescission or revision of the 2015 'Waters of the United States' rule and creates no right, benefit, property or fund (sec. 4(c) disclaims rights); rulemakings carried out under it were independent exercises of statutory authority, not rights or duties of the order, and sec. 7(f) points to rescission rather than preservation. S0 prefill (none_after_bounded_search) KEPT. Bounded search: EO 13778, EO 13790 and EO 13990 in full; a by-number scan of all held FR-original texts."),
 '13792': ("none_after_bounded_search",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13792 with no savings, pending-matter or transition clause; sec. 8(a) saves only statutory agency authority; sec. 7(f) tells the OMB Director and agency heads to rescind issuances implementing or enforcing the revoked orders; nothing is transferred. Own-residual check, reading EO 13792 in full: it orders a review of national monument designations and two reports and creates no right, benefit, property or fund (sec. 3(c) disclaims rights); it designates, modifies and withdraws nothing itself. Any later Presidential proclamation about monument boundaries was a separate act under the Antiquities Act, and EO 13990 sec. 3 reviews those proclamations on its own terms, so none is a surviving effect of this order. S0 prefill (none_after_bounded_search) KEPT. Bounded search: EO 13792 and EO 13990 in full; a by-number scan of all held FR-original texts."),
 '13795': ("continuing_independent",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13795 with no savings clause; sec. 8(a) saves only statutory agency authority; sec. 7(f) tells the OMB Director and agency heads to rescind issuances implementing or enforcing the revoked orders; sec. 4(b) reinstates EO 13754 and the December 20, 2016 memorandum 'in their original form' and names no other memorandum. Own-residual check, reading EO 13795 in full: sec. 5 is self-executing. It modifies 'to read, in its entirety' the body text of three OCS withdrawal memoranda (December 20, 2016; January 27, 2015; July 14, 2008), withdrawing the sanctuary areas 'for a time period without specific expiration', and adds that 'nothing in the withdrawal under this section affects any rights under existing leases'. A modification already made to other Presidential instruments, and a lease-rights proviso, do not lapse when the modifying order is revoked. EO 13990 sec. 4(b) undoes the change only for the December 20, 2016 memorandum (and EO 13754, revoked by sec. 4(c)); it does not mention the January 27, 2015 or July 14, 2008 memoranda, so by its terms their text as modified stays. S0 prefill (none_after_bounded_search) OVERRULED: the prefill finds no savings wording because EO 13990 has none, but the order's own sec. 5 effect continues under the memoranda themselves (OCSLA sec. 12(a)). Bounded search: EO 13795, EO 13990 in full; a by-number scan of all held FR-original texts (EO 13754 appears only in EO 13795 and EO 13990); U.S. Code notes to 15 U.S.C. 4101 and 43 U.S.C. 1331. The status of the 2015 and 2008 memoranda today is not searched here."),
 '13868': ("none_after_bounded_search",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13868 with no savings, pending-matter or transition clause; sec. 8(a) saves only statutory agency authority; sec. 7(f) tells the OMB Director and agency heads to rescind issuances implementing or enforcing the revoked orders; nothing is transferred. Own-residual check, reading EO 13868 in full: it directs guidance, rulemakings, reviews and reports (Clean Water Act section 401, LNG rules, Labor review, rights-of-way renewals) and creates no right, benefit, property or fund (sec. 10(c) disclaims rights). Rules and guidance issued by EPA, DOT and others under it were independent exercises of statutory authority; the order set up no continuing body, and sec. 6's rights-of-way renewals are agency grants, not rights of the order. S0 prefill (none_after_bounded_search) KEPT. Bounded search: EO 13868 and EO 13990 in full; a by-number scan of all held FR-original texts; the U.S. Code note to 42 U.S.C. 13201 (repeats the revocation)."),
 '13927': ("none_after_bounded_search",
  "Reading record scale/readings/LSP-EO_13990.json (EO 13990, 86 FR 7037-7043, read once in full): sec. 7(a) revokes EO 13927 with no savings, pending-matter or transition clause; sec. 8(a) saves only statutory agency authority; sec. 7(f) tells the OMB Director and agency heads to rescind issuances implementing or enforcing the revoked orders; nothing is transferred. Own-residual check, reading EO 13927 in full: it directs agencies to expedite projects and to report once and then every 30 days for the duration of the national emergency; it creates no right, benefit, property or fund (sec. 10(c) disclaims rights) and no body. The recurring reports were continuing duties of the order, and the revocation ended them; nothing in EO 13990 keeps them running. Emergency actions agencies took under their own statutory authorities are independent of the order. S0 prefill (none_after_bounded_search) KEPT. Bounded search: EO 13927 and EO 13990 in full; a by-number scan of all held FR-original texts; the U.S. Code note to 5 U.S.C. 601 (repeats the revocation)."),
}

def build(n, d):
    o = ORDERS[n]
    clauses_spec = C[n]
    dos = {c['scope_id'].split('#')[1]: c for c in d['clauses']}
    overrides = []
    scope_map = {}  # spec key -> scope id
    if n in ('13766', '13868', '13927'):
        orig = d['original_source_id']
        for c in d['clauses']:
            key = c['scope_id'].split('#')[1]
            if n == '13868':
                if key == 'sec3-c-dup2':
                    continue
                new = {'sec3-i-dup2': 'sec3-b-i', 'sec3-i-ii-dup2': 'sec3-b-ii'}.get(key, key)
                start, end = c['char_start'], c['char_end']
                reason = 'Dossier span retained unchanged.'
                if key == 'sec3-d':
                    end = dos['sec3-c-dup2']['char_end']
                    reason = "Merged the dossier's trailing fragment 'sec3-c-dup2' (the tail of the sentence in Sec. 3(d), split at a line break) into Sec. 3(d); the two spans were adjacent."
                elif new != key:
                    reason = f"Dossier span retained; scope renamed from '{key}' to '{new}' because this span is Sec. 3(b){'(i)' if key=='sec3-i-dup2' else '(ii)'}, not a duplicate."
            elif n == '13766':
                new = key
                start, end = c['char_start'], c['char_end']
                reason = 'Dossier span retained unchanged.'
                if key == 'lead':
                    start = 742
                    reason = "Extended the dossier's 27-character lead 'I hereby direct as follows:' backwards to include the issuing words 'By the authority vested in me as President ...', so the clause text is long enough for the checker to verify; the end is unchanged."
            else:
                if key == 'sec8-a':
                    continue
                new = key
                start, end = c['char_start'], c['char_end']
                reason = 'Dossier span retained unchanged.'
                if key == 'sec8-c':
                    end = dos['sec8-a']['char_end']
                    reason = "Merged the dossier's trailing fragment 'sec8-a' ('(a)(i). Such status reports shall thereafter be provided...', the tail of the sentence in Sec. 8(c), split at a line break) into Sec. 8(c); the two spans were adjacent."
            overrides.append({"scope_id": f"EO:{n}#{new}", "source_id": orig, "char_start": start, "char_end": end, "reason": reason})
            scope_map[key] = new
    clauses = []
    for key, kind, desc in clauses_spec:
        scope_key = key
        if n in ('13766', '13868', '13927'):
            assert any(ov['scope_id'] == f"EO:{n}#{key}" for ov in overrides), (n, key)
        else:
            assert key in dos, (n, key)
        reason = desc + '. ' + TAIL[kind] + EXTRA_REASON.get((n, key), '')
        later = copy.deepcopy(LATER.get((n, key), []))
        clauses.append({
            "scope_id": f"EO:{n}#{key}", "state": "terminated",
            "end_id": f"ACT:EO:{n}>EO:13990", "effective_date": END_DATE, "effective_date_confirmed": True,
            "mechanism": mech(n), "reason": reason,
            "current_basis_id": None, "current_legal_basis": "", "checked_through": None,
            "later_event_ids": [], "later_events": later})
    # inventory completeness: spec must cover exactly the dossier/override scopes
    expected = [ov['scope_id'] for ov in overrides] if overrides else [c['scope_id'] for c in d['clauses']]
    got = [c['scope_id'] for c in clauses]
    assert sorted(expected) == sorted(got), (n, set(expected) ^ set(got))
    state, sav_reason = SAVINGS[n]
    sheet = {
        "schema": "eo-claim-kit-decision/v1", "instrument_id": f"EO:{n}",
        "dossier_sha256": d['fingerprint'], "agent": AGENT, "approved": True,
        "original_confirmed": True, "original_pages_confirmed": False, "inventory_confirmed": True,
        "inventory_overrides": overrides, "clauses": clauses, "conflict_resolutions": {},
        "savings": {"state": state, "source_id": "ACTOR_TEXT:EO:13990", "reason": sav_reason},
        "search_ids": ["current-law:usc", "current-law:ecfr", "later-events:ofr_catalog"],
        "research_rationale": RATIONALE[n], "unresolved_material_gaps": []}
    return sheet

if __name__ == '__main__':
    for n in ['13766', '13778', '13792', '13795', '13868', '13927']:
        d = json.load(open(S + f'd{n}.json'))
        sh = build(n, d)
        json.dump(sh, open(OUT + f'EO_{n}.json', 'w'), indent=1, ensure_ascii=False)
        print(n, len(sh['clauses']), len(sh['inventory_overrides']), sh['savings']['state'])
