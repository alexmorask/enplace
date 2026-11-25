"""Shared helpers for Enplace's Droid hooks.

Hooks get a JSON event on stdin. For PreToolUse that includes `tool_name`
and `tool_input`. The exact field names inside `tool_input` differ by tool
(Create, Edit, ApplyPatch, Execute), so these helpers read them defensively.

To block an action: print the reason to stderr and exit 2.
"""

import json
import os
import re
import sys

PATCH_PATH_RE = re.compile(
    r"^(?:\*\*\* (?:Add|Update|Delete) File: |\+\+\+ b/|--- a/)(.+?)\s*$",
    re.MULTILINE,
)


def read_event():
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def allow():
    sys.exit(0)


def project_dir():
    return os.environ.get("FACTORY_PROJECT_DIR") or os.getcwd()


def rel(path):
    """Path relative to the repo root, with forward slashes."""
    root = os.path.realpath(project_dir())
    full = os.path.realpath(os.path.join(root, path))
    if full.startswith(root + os.sep):
        full = full[len(root) + 1 :]
    return full.replace(os.sep, "/")


def _walk(value, key=""):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from _walk(v, k)
    elif isinstance(value, list):
        for v in value:
            yield from _walk(v, key)
    elif isinstance(value, str):
        yield key.lower(), value


def tool_input(event):
    return event.get("tool_input") or {}


def command(event):
    """The shell command for an Execute call."""
    ti = tool_input(event)
    for key in ("command", "cmd"):
        if isinstance(ti.get(key), str):
            return ti[key]
    return " ".join(v for _, v in _walk(ti))


def paths(event):
    """Every file path an edit-type tool call touches."""
    found = []
    for key, value in _walk(tool_input(event)):
        if "path" in key or key in ("file", "filename", "target"):
            found.append(value)
        found.extend(m.group(1) for m in PATCH_PATH_RE.finditer(value))
    return sorted({rel(p) for p in found if p and "\n" not in p})


def old_and_new_text(event):
    """(old, new) text for an edit. Old is '' if unknown."""
    old, new = [], []
    for key, value in _walk(tool_input(event)):
        if "path" in key:
            continue
        if "old" in key:
            old.append(value)
        elif "new" in key or key in ("content", "contents", "text"):
            new.append(value)
        elif "patch" in key or key == "input":
            for line in value.splitlines():
                if line.startswith("-") and not line.startswith("---"):
                    old.append(line[1:])
                elif line.startswith("+") and not line.startswith("+++"):
                    new.append(line[1:])
    return "\n".join(old), "\n".join(new)


def file_on_disk(path):
    try:
        with open(os.path.join(project_dir(), path), encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""
