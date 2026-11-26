"""Hook 3: protect the guardrails.

Droids may read but never change AGENTS.md (at any level) or anything
under .factory/. Alex edits these by hand. GitHub workflows are open to
droids; AGENTS.md rule 6 and the reviewer droid cover them.
"""

import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _common import allow, block, command, paths, read_event  # noqa: E402

PROTECTED = re.compile(r"(^|/)AGENTS\.md$|^\.factory/", re.I)
PROTECTED_IN_SHELL = re.compile(r"AGENTS\.md|\.factory/|\.factory\b", re.I)
WRITES = re.compile(
    r">|\btee\b|\bsed\s+-i|\bperl\s+-i|\bmv\b|\bcp\b|\brm\b|\bchmod\b|\btruncate\b|"
    r"\bgit\s+(checkout|restore|rm|mv)\b|\bpython3?\b|\bnode\b"
)

REASON = (
    "Blocked: AGENTS.md and .factory/ are edited by hand only "
    "(AGENTS.md, top of file). If a rule needs changing, explain why in the PR."
)

event = read_event()

if event.get("tool_name") == "Execute":
    cmd = command(event)
    if PROTECTED_IN_SHELL.search(cmd) and WRITES.search(cmd):
        block(REASON)
    allow()

if any(PROTECTED.search(p) for p in paths(event)):
    block(REASON)

allow()
