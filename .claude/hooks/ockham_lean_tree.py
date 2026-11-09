"""Ockham: refuse agent commands that list or search the whole repository tree.

Named for William of Ockham's razor: do not multiply entities beyond necessity. The tree holds about 194,000
tracked files and roughly 97% of them are job outputs, data, attempt receipts and frozen work papers. One
unbounded `git ls-files`, `find .` or root-wide `**` glob returns megabytes that the tool then cuts off,
spending tokens on paths no one wanted. This Claude Code PreToolUse hook refuses those few commands and says
what to run instead; everything else passes. A listing piped into another command (head, wc, grep) is the
agent filtering on purpose and passes too. It never blocks a command it cannot parse (it fails open).

Exit 2 with a message on stderr is Claude Code's "refuse and tell the model why".
"""
import json
import re
import shlex
import sys

ADVICE = ("Ockham (.claude/hooks/ockham_lean_tree.py): this would list the whole ~194,000-file tree. "
          "Name a folder instead, for example `git ls-files -- jobs/kean | head -50`, "
          "`find jobs/kean -maxdepth 2`, Glob with a path such as jobs/kean, or Grep, which skips outputs "
          "and data by default (.ignore). HANDOFF/README.md and jobs/README.md map the repository.")

ROOT_WORDS = {".", "./", "*", "", "/", "~"}
OPERATORS = {"|", "||", "&&", ";", "&", ";;", "|&"}
# git ls-files modes whose output is small whatever the tree size (conflicts, untracked, changed files).
SMALL_LS_FILES = {"-u", "--unmerged", "-o", "--others", "-m", "--modified", "-d", "--deleted", "-k", "--killed"}
GIT_VALUE_OPTIONS = {"-c", "-C", "--git-dir", "--work-tree", "--namespace"}
GLOB_CHARS = set("*?[{")


def _words(command):
    """Shell words with operators as separate words and newlines as `;`; None if unparseable."""
    lexer = shlex.shlex(command.replace("\r", "").replace("\n", " ; "), posix=True, punctuation_chars=";&|")
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return None


def _pipelines(words):
    """Yield (simple command, piped onward) pairs."""
    segment = []
    for word in words + [";"]:
        if word in OPERATORS:
            if segment:
                yield segment, word in {"|", "|&"}
            segment = []
        else:
            segment.append(word)


def _ls_files_refusal(args):
    rest = list(args)
    if any(a in SMALL_LS_FILES or a.startswith("--others") for a in rest):
        return None
    if "--" in rest:
        paths = rest[rest.index("--") + 1:]
    else:
        paths = [a for a in rest if not a.startswith("-")]
    if paths and not all(p in ROOT_WORDS for p in paths):
        return None
    return ADVICE


def _find_refusal(args):
    starts = []
    for arg in args:
        if arg.startswith("-") or arg in {"(", "!", ","}:
            break
        starts.append(arg)
    if "-maxdepth" in args:
        return None
    if not starts or all(s in ROOT_WORDS for s in starts):
        return ADVICE
    return None


def bash_refusal(command):
    words = _words(command)
    if words is None:
        return None
    narrowed = False  # an earlier `cd <folder>` moved the command below the repository root
    for seg, piped in _pipelines(words):
        while seg and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", seg[0]):
            seg = seg[1:]  # VAR=value prefixes
        if not seg:
            continue
        name = seg[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
        if name.endswith(".exe"):
            name = name[:-4]
        args = seg[1:]
        if name in {"cd", "pushd", "set-location", "sl"}:
            target = next((a for a in args if not a.startswith("-")), "")
            narrowed = target not in ROOT_WORDS and target != ".."
            continue
        if piped or narrowed:
            continue
        refusal = None
        if name == "git":
            i = 0
            while i < len(args) and args[i].startswith("-"):
                if args[i] in GIT_VALUE_OPTIONS:
                    if args[i] == "-C" and i + 1 < len(args) and args[i + 1] not in ROOT_WORDS:
                        break  # git -C <folder> runs below the root
                    i += 1
                i += 1
            else:
                if args[i:i + 1] == ["ls-files"]:
                    refusal = _ls_files_refusal(args[i + 1:])
        elif name == "find":
            refusal = _find_refusal(args)
        elif name in {"ls", "dir"}:
            recursive = any(re.fullmatch(r"-[A-Za-z]*R[A-Za-z]*", a) or a == "--recursive" for a in args)
            targets = [a for a in args if not a.startswith("-")]
            if recursive and all(t in ROOT_WORDS for t in targets):
                refusal = ADVICE
        elif name == "tree":
            targets = [a for a in args if not a.startswith("-")]
            if all(t in ROOT_WORDS for t in targets) and "-L" not in args:
                refusal = ADVICE
        # PowerShell accepts any prefix of -Recurse; `dir` is its alias too (Unix `ls -r` only reverses).
        if name in {"get-childitem", "gci", "dir"}:
            recursive = any(len(a) >= 2 and "-recurse".startswith(a.lower()) for a in args)
            targets = [a for a in args if not a.startswith("-")]
            if recursive and "-depth" not in [a.lower() for a in args] and all(t in ROOT_WORDS for t in targets):
                refusal = ADVICE
        if refusal:
            return refusal
    return None


def glob_refusal(tool_input, project_dir):
    pattern = str(tool_input.get("pattern") or "").replace("\\", "/")
    path = str(tool_input.get("path") or "").replace("\\", "/").rstrip("/")
    root = str(project_dir or "").replace("\\", "/").rstrip("/")
    at_root = not path or path in ROOT_WORDS or (root and path.lower() == root.lower())
    if not at_root or "**" not in pattern:
        return None
    first = pattern.lstrip("./").split("/", 1)[0]
    if pattern.startswith("**") or GLOB_CHARS & set(first):
        return ADVICE
    return None


def main():
    try:
        event = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if not isinstance(event, dict):
        return 0
    tool = event.get("tool_name")
    tool_input = event.get("tool_input") or {}
    if tool in {"Bash", "PowerShell"}:
        message = bash_refusal(str(tool_input.get("command") or ""))
    elif tool == "Glob":
        message = glob_refusal(tool_input, event.get("cwd"))
    else:
        message = None
    if message:
        print(message, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
