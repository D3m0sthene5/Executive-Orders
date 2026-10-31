"""Bind runner results to the code and declared repository inputs actually read.

Git object IDs avoid rereading unchanged corpus files. Modified/untracked inputs
are hashed from disk, including outputs generated earlier in this invocation.
External servers and undeclared reads cannot be versioned by this guard.

jobs/<name>/inputs.txt declares additional repository reads as fnmatch patterns
(like triggers.txt, * spans directory separators). It versions additions as
well as existing files. Use needs.txt for literal directory roots. The prepare
command materializes matching tracked sparse inputs before a job starts.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

MANIFEST = "RUNNER_INPUTS.json"
NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
VALLA_CERTIFICATE_ROOTS = ['jobs/valla', 'jobs/_lib',
                           '.github/scripts/materialize_job_inputs.py',
                           '.github/scripts/result_freshness.py',
                           '.github/scripts/run_jobs.py', '.github/scripts/run_jobs.sh',
                           '.github/workflows/run-jobs.yml']


def valla_implementation_scope():
    return {'roots': VALLA_CERTIFICATE_ROOTS, 'patterns': [], 'exclude': 'jobs/valla/output'}


def valla_signature(ref='HEAD'):
    return digest(tree(ref, valla_implementation_scope()))


def valla_certified():
    try:
        certificate = json.loads(Path(__file__).with_name('materialization_certificates.json').read_text('utf-8'))['valla']
        return (not any(v.startswith('120000:') for v in tree('HEAD', valla_implementation_scope()).values())
                and isinstance(certificate, str) and re.fullmatch('[0-9a-f]{64}', certificate)
                and valla_signature() == certificate
                and digest(working(valla_implementation_scope())) == certificate)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        return False


def git(*args, input=None):
    return subprocess.run(["git", *args], input=input, capture_output=True, check=True).stdout


def lines(path):
    p = Path(path)
    if not p.exists():
        return []
    return [s for line in p.read_text(encoding="utf-8").splitlines()
            if (s := line.split("#", 1)[0].strip())]


def valla_references():
    """Resolve runner build's explicit review pointers, including sparse providers.

    This is an engineering read closure, not review validation. Over-select fields
    even in refused records; Valla remains the authority for their meaning.
    Unsupported metadata restores the broad repository instead of guessing.
    """
    folders = ('research/readiness/method_reviews',
               'research/readiness/component_attestations')
    providers = {}
    try:
        inventory = git('ls-files', '-t', '-z', '--', *folders)
    except subprocess.CalledProcessError:
        return [], False
    for record in inventory.split(b'\0'):
        if record:
            tag, raw = record.split(b' ', 1)
            p = raw.decode('utf-8')
            if str(PurePosixPath(p).parent) in folders and p.endswith('.jsonl'):
                providers[p] = tag == b'S'
    for folder in folders:
        for p in Path(folder).glob('*.jsonl'):
            providers.setdefault(p.as_posix(), False)
    root = Path.cwd().resolve()
    references = set(providers)
    ancestors = set()

    def add(value):
        if not isinstance(value, str):
            raise ValueError('non-string Valla reference')
        raw = Path(value)
        if '..' in raw.parts:
            raise ValueError('parent traversal Valla reference')
        lexical = Path(os.path.abspath(root / raw))
        # Symlink resolution depends on checkout state. Decline narrowing for
        # either a live or tracked symlink, including a sparse ancestor.
        if lexical.is_relative_to(root):
            parts = lexical.relative_to(root).parts
            for i in range(1, len(parts) + 1):
                p = root.joinpath(*parts[:i])
                ancestors.add(p.relative_to(root).as_posix())
                if p.is_symlink():
                    raise ValueError('symlink Valla reference')
        resolved = lexical.resolve()
        # Valla.safe refuses external paths before reading them.
        if not resolved.is_relative_to(root):
            return
        rel = resolved.relative_to(root).as_posix()
        if rel == '.':
            raise ValueError('repository directory reference')
        references.add(rel)
        for p in references:
            if any(c in p for c in ('\n', '\r', '\\', ':')):
                raise ValueError('unsupported Valla reference path')

    try:
        for provider, sparse in providers.items():
            path = Path(provider)
            add(provider)
            if path.exists():
                raw = path.read_bytes()
            elif sparse:
                raw = git('show', 'HEAD:' + provider)
            else:
                continue  # A working deletion is not an old HEAD provider.
            for line in raw.decode('utf-8').splitlines():
                if not line.strip():
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError('non-object Valla record')
                for field in ('review_ref', 'reviewed_claim_ref'):
                    if field in record:
                        add(record[field]['path'])
                for dep in record.get('dependencies', []):
                    if dep['kind'] in ('file', 'rule'):
                        add(dep['key'])
        if ancestors:
            entries = git('ls-tree', '-z', 'HEAD', '--', *(':(literal)' + p for p in sorted(ancestors)))
            for entry in entries.split(b'\0'):
                if entry:
                    header, raw = entry.split(b'\t', 1)
                    if header.startswith(b'120000 ') and raw.decode() in ancestors:
                        raise ValueError('tracked symlink Valla reference')
    except (ValueError, KeyError, TypeError, AttributeError, OSError, RuntimeError, UnicodeError, subprocess.CalledProcessError):
        return [], False
    return sorted(references), True


def valla_linked_inputs(declared):
    """Every read family can contain an alias, including fixed protocol paths."""
    entries = tracked_entries('HEAD', declared)
    paths = set(entries) | set(literal_prefixes(declared))
    ancestors = {str(parent) for p in paths for parent in (PurePosixPath(p), *PurePosixPath(p).parents)
                 if str(parent) != '.'}
    if any(Path(p).is_symlink() for p in ancestors):
        return True
    if ancestors:
        metadata = git('ls-tree', '-z', 'HEAD', '--', *(':(literal)' + p for p in sorted(ancestors)))
        for entry in metadata.split(b'\0'):
            if entry:
                header, raw = entry.split(b'\t', 1)
                if header.startswith(b'120000 ') and raw.decode() in ancestors:
                    return True
    return False


def valla_direct_reads(patterns):
    """Live fixed reads and sheet siblings of Git-discovered packages.

    Valla does not apply Git ignore rules when opening these files. Retain
    absent siblings too, so arrivals and deletions remain observable.
    """
    paths = {p for p in patterns if not re.search(r'[*?\[]', p)}
    for folder in ('claims', 'component_attestations', 'method_reviews'):
        paths.update(p.as_posix() for p in Path('research/readiness', folder).glob('*.jsonl'))
    registry = git('ls-files', '-z', '--', 'research/excavator/**/RATIONALES.json',
                   'research/production/**/RATIONALES.json')
    for raw in registry.split(b'\0'):
        if raw:
            folder = PurePosixPath(raw.decode('utf-8')).parent
            paths.update(str(folder / name) for name in ('RATIONALES.json', 'decisions.csv', 'clauses.csv'))
    return paths


def scope(name):
    if not NAME.fullmatch(name):
        raise ValueError(f"Invalid job name: {name!r}")
    roots = [f"jobs/{name}", "jobs/_lib", ".github/scripts", ".github/workflows/run-jobs.yml"]
    roots += lines(f"jobs/{name}/needs.txt")
    predecessors = lines(f"jobs/{name}/after.txt")
    if any(not NAME.fullmatch(dep) for dep in predecessors):
        raise ValueError(f"Invalid after.txt dependency for {name}")
    roots += [f"jobs/{dep}/output" for dep in predecessors]
    patterns = lines(f"jobs/{name}/triggers.txt") + lines(f"jobs/{name}/inputs.txt")
    # This job explicitly enumerates the corpus, rather than just after.txt.
    if name == "daily-digest":
        patterns += ["jobs/*/output/SUMMARY.json", "jobs/*/output/STATUS.json", "HANDOFF/notes-*.md"]
    referenced_files = []
    dynamic_complete = True
    implementation_certified = False
    if name == 'valla':
        referenced_files, dynamic_complete = valla_references()
        implementation_certified = bool(valla_certified())
        referenced_files = sorted(set(referenced_files) | valla_direct_reads(patterns))
        roots += referenced_files
        if dynamic_complete and valla_linked_inputs({'roots': roots, 'patterns': patterns,
                                                     'exclude': f'jobs/{name}/output'}):
            dynamic_complete = False
        if not dynamic_complete or not implementation_certified:
            patterns += ['*']
    for value in roots + patterns:
        p = PurePosixPath(value)
        if p.is_absolute() or ".." in p.parts or "\\" in value or ":" in value:
            raise ValueError(f"Unsafe input declaration: {value!r}")
    result = {"roots": sorted(set(p.rstrip("/") for p in roots)),
              "patterns": sorted(set(patterns)), "exclude": f"jobs/{name}/output"}
    if name == 'valla':
        result.update(referenced_files=referenced_files, dynamic_complete=dynamic_complete,
                      implementation_certified=implementation_certified)
    return result


def under(path, root):
    return path == root or path.startswith(root + "/")


def literal_prefixes(declared):
    """Return conservative Git pathspec prefixes for a declared scope.

    Git is only asked to enumerate below these literal prefixes; ``select``
    remains the authority for fnmatch semantics (where ``*`` also spans ``/``).
    """
    prefixes = set(declared["roots"])
    for pattern in declared["patterns"]:
        wildcard = re.search(r"[*?\[]", pattern)
        prefix = pattern[:wildcard.start()] if wildcard else pattern
        if prefix.endswith("/"):
            prefix = prefix[:-1]
        elif wildcard and "/" in prefix:
            # A partial basename is not a literal path prefix (e.g. notes-*
            # cannot be passed as HANDOFF/notes- with :(literal)). Keep its
            # enclosing directory instead. With no slash, scope from the root.
            prefix = prefix.rsplit("/", 1)[0]
        elif wildcard:
            prefix = "."
        if prefix:
            prefixes.add(prefix)
        else:
            prefixes.add(".")
    # An ancestor prefix already covers all descendants.
    result = []
    for prefix in sorted(prefixes, key=lambda value: (value.count("/"), value)):
        if not any(parent == "." or under(prefix, parent) for parent in result):
            result.append(prefix)
    return result


def _pathspec(prefix):
    return ":(literal)" + prefix


def tracked_paths(ref, declared):
    """List exact tracked paths that may belong to a declared scope.

    Candidate enumeration is bounded by literal prefixes. The final result is
    still filtered by ``select`` so Git pathspec details cannot broaden scope.
    """
    return sorted(tracked_entries(ref, declared))


def tracked_entries(ref, declared):
    """Return matching tracked ``path -> mode:oid`` entries from Git metadata."""
    prefixes = literal_prefixes(declared)
    candidates = {}
    if prefixes:
        records = git("ls-tree", "-r", "-z", ref, "--", *(_pathspec(p) for p in prefixes))
        for record in records.split(b"\0"):
            if record:
                header, raw_path = record.split(b"\t", 1)
                mode, kind, oid = header.decode().split()
                candidates[raw_path.decode("utf-8")] = mode + ":" + oid
    return select(candidates, declared)


def select(entries, declared):
    return {p: value for p, value in entries.items()
            if not under(p, declared["exclude"])
            and (any(under(p, root) for root in declared["roots"])
                 or any(fnmatch.fnmatchcase(p, pat) for pat in declared["patterns"]))}


def tree(ref, declared=None):
    entries = {}
    if declared is None:
        records = git("ls-tree", "-r", "-z", ref).split(b"\0")
    else:
        prefixes = literal_prefixes(declared)
        records = (git("ls-tree", "-r", "-z", ref, "--", *(_pathspec(p) for p in prefixes)).split(b"\0")
                   if prefixes else [])
    for record in records:
        if record:
            header, path = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            entries[path.decode("utf-8")] = mode + ":" + oid
    return entries if declared is None else select(entries, declared)


def prepare(name):
    """Acquire declared inputs without expanding unrelated sparse directories."""
    declared = scope(name)
    sparse = subprocess.run(["git", "config", "--bool", "core.sparseCheckout"], capture_output=True)
    if sparse.stdout.strip() != b"true":
        return
    directories = set()
    prefixes = literal_prefixes(declared)
    if prefixes:
        for record in git("ls-files", "-t", "-z", "--", *(_pathspec(p) for p in prefixes)).split(b"\0"):
            if not record:
                continue
            tag, raw = record.split(b" ", 1)
            path = raw.decode("utf-8")
            if tag == b"S" and select({path: ""}, declared):
                directories.add(str(PurePosixPath(path).parent))
    if directories:
        # --stdin keeps a broad dynamic catalogue below Windows/Unix argv
        # limits. Cone mode intentionally includes each matched parent folder.
        git("sparse-checkout", "add", "--stdin", input=("\n".join(sorted(directories)) + "\n").encode())
        print(f"Materialized declared input directories for {name}: {len(directories)}")


def working(declared=None):
    entries = {}
    forced = []
    prefixes = None if declared is None else literal_prefixes(declared)
    args = ["ls-files", "--stage", "-t", "-z"]
    if prefixes is not None and prefixes:
        args += ["--", *(_pathspec(p) for p in prefixes)]
    for record in git(*args).split(b"\0") if prefixes is None or prefixes else []:
        if not record:
            continue
        header, path = record.split(b"\t", 1)
        tag, mode, oid, stage = header.decode().split()
        p = path.decode("utf-8")
        if declared is not None and not select({p: ""}, declared):
            continue
        if stage != "0":
            raise ValueError(f"Unmerged input: {p}")
        if tag == "S":
            if not Path(p).exists() and not Path(p).is_symlink():
                raise ValueError(f"Declared input is absent from sparse checkout: {p}; run result_freshness.py prepare before capture")
            forced.append(p)
        entries[p] = mode + ":" + oid
    changed_paths = set()
    # Exact record pointers can name ignored caches or same-run untracked files.
    # Git's --exclude-standard inventory cannot version those bytes by itself.
    if declared is not None:
        changed_paths.update(declared.get('referenced_files', []))
    if prefixes is None:
        args = ["ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z"]
        changed = git(*args)
        changed_paths.update(p.decode("utf-8") for p in changed.split(b"\0") if p)
    elif prefixes:
        args = ["ls-files", "--modified", "--deleted", "--others", "--exclude-standard", "-z", "--",
                *(_pathspec(p) for p in prefixes)]
        changed = git(*args)
        changed_paths.update(p.decode("utf-8") for p in changed.split(b"\0") if p)
    paths = sorted(changed_paths | set(forced))
    if declared is not None:
        paths = [p for p in paths if select({p: ""}, declared)]
    files = []
    for p in paths:
        path = Path(p)
        if path.is_symlink():
            data = os.readlink(path).encode()
            entries[p] = "120000:" + hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        elif path.is_file():
            if "\n" in p or '"' in p:
                raise ValueError(f"Unsupported input filename: {p!r}")
            files.append(p)
        else:
            entries.pop(p, None)
    if files:
        hashes = git("hash-object", "--stdin-paths", input=("\n".join(files) + "\n").encode()).decode().splitlines()
        for p, oid in zip(files, hashes, strict=True):
            mode = entries.get(p, "100755:" if os.name != "nt" and os.access(p, os.X_OK) else "100644:").split(":")[0]
            entries[p] = mode + ":" + oid
    return entries


def digest(entries):
    return hashlib.sha256(json.dumps(entries, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def output(entries, name):
    return {p: v for p, v in entries.items() if under(p, f"jobs/{name}/output")}


def capture(name, destination):
    declared = scope(name)
    inputs = working(declared)
    base = git("rev-parse", "HEAD").decode().strip()
    base_output_scope = {"roots": [f"jobs/{name}/output"], "patterns": [], "exclude": "\0"}
    manifest = {"schema": 1, "job": name, "base_commit": base,
                "run_url": os.environ.get("RUN_URL") or
                f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                "scope": declared, "inputs_sha256": digest(inputs), "inputs": inputs,
                "base_output_sha256": digest(output(tree(base, base_output_scope), name))}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def check(ref, names, report):
    candidate = working({"roots": [f"jobs/{name}/output" for name in names], "patterns": [], "exclude": "\0"})
    base_output_scope = {"roots": [f"jobs/{name}/output" for name in names], "patterns": [], "exclude": "\0"}
    problems, manifests, bases = [], {}, {}
    for name in names:
        p = Path("jobs") / name / "output" / MANIFEST
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            if m["schema"] != 1 or m["job"] != name or digest(m["inputs"]) != m["inputs_sha256"]:
                raise ValueError("Invalid provenance manifest")
            declared = m["scope"]
            if name == 'valla' and declared.get('dynamic_complete') is not True:
                raise ValueError('Unresolved Valla read closure; full fallback is available but publication requires a closed input scope')
            if (not isinstance(m["inputs"], dict)
                    or not all(isinstance(declared[k], list) for k in ("roots", "patterns"))
                    or declared["exclude"] != f"jobs/{name}/output"
                    or not isinstance(m["base_output_sha256"], str)):
                raise ValueError("Invalid provenance scope or baseline")
            base = m["base_commit"]
            if not isinstance(base, str) or not re.fullmatch(r"[0-9a-f]{40,64}", base):
                raise ValueError("Invalid provenance base commit")
            if base not in bases:
                bases[base] = tree(base, base_output_scope)
            if digest(output(bases[base], name)) != m["base_output_sha256"]:
                raise ValueError("Provenance output baseline does not match its commit")
            manifests[name] = m
        except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
            problems.append({"job": name, "reason": "missing_or_invalid_manifest", "detail": str(exc)})
            continue
    if manifests:
        combined = {"roots": sorted({p for m in manifests.values() for p in m["scope"]["roots"]}
                                     | {f"jobs/{name}/output" for name in names}),
                    "patterns": sorted({p for m in manifests.values() for p in m["scope"]["patterns"]}),
                    "exclude": "\0"}
        latest = tree(ref, combined)
    else:
        latest = {}
    for name, m in manifests.items():
        branch_output = digest(output(latest, name))
        if branch_output not in (m["base_output_sha256"], digest(output(candidate, name))):
            problems.append({"job": name, "reason": "concurrent_output_advanced",
                             "detail": "The branch's output changed after this run's checkout. Rerun on the current branch."})
    # Each consumer may have read a prior job's candidate or a later job's base
    # generation. Never substitute a later-produced candidate into that earlier
    # snapshot. The whole-output concurrency check above remains authoritative.
    generations = {}
    run_order = {name: position for position, name in enumerate(names)}
    for name, m in manifests.items():
        expected, projected = m["inputs"], dict(latest)
        generations[name] = {}
        for producer in names:
            produced = output(candidate, producer)
            baseline = output(bases[m["base_commit"]], producer)
            captured = output(expected, producer)
            candidate_inputs = select(produced, m["scope"])
            base_inputs = select(baseline, m["scope"])
            if not (captured or candidate_inputs or base_inputs):
                continue
            generation = "same_run_candidate"
            chosen = produced
            if captured != candidate_inputs:
                if (run_order[producer] > run_order[name] and captured == base_inputs
                        and output(latest, producer) == baseline):
                    chosen, generation = baseline, "captured_base"
                else:
                    generation = "unmatched"
            generations[name][producer] = generation
            projected = {p: v for p, v in projected.items() if not under(p, f"jobs/{producer}/output")}
            projected.update(chosen)
        if name == 'valla':
            # Direct file reads may include ignored live files or previously
            # absent targets. Recheck after execution; do not substitute a
            # later selected producer's generation for the captured one.
            current_scope = scope('valla')
            if not current_scope['dynamic_complete']:
                problems.append({'job': name, 'reason': 'unresolved_read_closure_after_execution'})
            refs = [p for p in set(m['scope'].get('referenced_files', []))
                    | set(current_scope.get('referenced_files', []))
                    if not any(under(p, f'jobs/{producer}/output') for producer in names)]
            direct_scope = {'roots': refs, 'patterns': [], 'exclude': f'jobs/{name}/output',
                            'referenced_files': refs}
            before, after = select(expected, direct_scope), working(direct_scope)
            if before != after:
                problems.append({'job': name, 'reason': 'referenced_input_changed_during_run',
                                 'changed_paths': [{'path': p, 'captured': before.get(p), 'working': after.get(p)}
                                                   for p in sorted(before.keys() | after.keys())
                                                   if before.get(p) != after.get(p)]})
            if m['scope'].get('implementation_certified') and not valla_certified():
                problems.append({'job': name, 'reason': 'certified_implementation_changed_during_run'})
        expected, actual = m["inputs"], select(projected, m["scope"])
        changed = sorted(p for p in expected.keys() | actual.keys() if expected.get(p) != actual.get(p))
        if changed:
            problems.append({"job": name, "reason": "inputs_changed", "captured_inputs_sha256": m["inputs_sha256"],
                             "branch_inputs_sha256": digest(actual), "changed_path_count": len(changed),
                             "changed_paths": [{"path": p, "captured": expected.get(p), "branch": actual.get(p)} for p in changed]})
    result = {"schema": 1, "result": "rejected" if problems else "fresh", "branch_commit": git("rev-parse", ref).decode().strip(),
              "jobs": names, "problems": problems, "input_generations": generations,
              "action": "Rerun these jobs on the current branch; retained outputs were not published." if problems else "Publish only while this branch commit remains current."}
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if problems:
        # The workflow's artifact-upload step precedes commit, so its summary
        # and log are the durable locations for commit-time rejection details.
        rendered = json.dumps(result, indent=2)
        print("::error::Runner results rejected as stale. " + result["action"])
        print(rendered)
        if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
            with open(summary, "a", encoding="utf-8") as fh:
                fh.write("\n### Runner freshness rejection\n\n```json\n" + rendered + "\n```\n")
        return 3
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    acquire = sub.add_parser("prepare")
    acquire.add_argument("job")
    cap = sub.add_parser("capture")
    cap.add_argument("job")
    cap.add_argument("destination", type=Path)
    verify = sub.add_parser("check")
    verify.add_argument("ref")
    verify.add_argument("report", type=Path)
    verify.add_argument("jobs", nargs="+")
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args.job)
        return 0
    if args.command == "capture":
        capture(args.job, args.destination)
        return 0
    return check(args.ref, args.jobs, args.report)


if __name__ == "__main__":
    sys.exit(main())
