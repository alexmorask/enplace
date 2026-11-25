"""Hook 2: no weakening tests.

Blocks, for test files:
- adding .skip / .only / .todo (or xit / xdescribe / fit)
- removing tests or assertions (fewer `test(`/`it(` or `expect(` than before)
- deleting or moving test files from the shell

It can't see whether a test is currently failing, so the full rule
("never edit a failing test") also lives in AGENTS.md rule 2.
"""

import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _common import (  # noqa: E402
    allow,
    block,
    command,
    file_on_disk,
    old_and_new_text,
    paths,
    read_event,
)

TEST_FILE = re.compile(r"\.(test|spec)\.[cm]?[jt]sx?$|(^|/)tests/")
SKIPS = re.compile(r"\b(?:it|test|describe)\.(?:skip|only|todo)\b|\b(?:xit|xdescribe|fit|fdescribe)\s*\(")
TESTS = re.compile(r"\b(?:it|test)\s*\(")
ASSERTS = re.compile(r"\bexpect\s*\(|\bassert\.")

REASON = "Blocked: {what} in {path}. Fix the code, not the test (AGENTS.md rule 2)."

event = read_event()

if event.get("tool_name") == "Execute":
    cmd = command(event)
    if re.search(r"\b(rm|git\s+rm|mv|git\s+mv)\b", cmd) and re.search(
        r"\.(test|spec)\.[cm]?[jt]sx?\b|\btests/", cmd
    ):
        block("Blocked: deleting or moving test files from the shell (AGENTS.md rule 2).")
    allow()

test_paths = [p for p in paths(event) if TEST_FILE.search(p)]
if not test_paths:
    allow()

old, new = old_and_new_text(event)
for path in test_paths:
    before = old or file_on_disk(path)
    if len(SKIPS.findall(new)) > len(SKIPS.findall(before)) and not SKIPS.findall(before):
        block(REASON.format(what="adding skip/only/todo", path=path))
    if before:
        if len(TESTS.findall(new)) < len(TESTS.findall(before)):
            block(REASON.format(what="removing tests", path=path))
        if len(ASSERTS.findall(new)) < len(ASSERTS.findall(before)):
            block(REASON.format(what="removing assertions", path=path))

allow()
