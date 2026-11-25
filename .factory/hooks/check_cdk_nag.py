"""Hook 5: cdk-nag must pass before finishing a change to infra/.

Runs when a droid is about to end its turn. If anything under infra/ changed
on this branch (or is uncommitted), it runs `pnpm nag`. If that fails, the
turn doesn't end: the failure output becomes the droid's next instruction.

Skipped until the `nag` script exists (it's added in M0 issue 1).
"""

import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from _common import allow, project_dir, read_event  # noqa: E402


def git(*args):
    result = subprocess.run(
        ["git", *args], cwd=project_dir(), capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else ""


event = read_event()

if event.get("stop_hook_active"):
    # Already blocked once this turn. Don't loop forever; warn instead.
    print(json.dumps({"systemMessage": "cdk-nag still failing; see the droid's last output."}))
    allow()

try:
    with open(os.path.join(project_dir(), "package.json"), encoding="utf-8") as f:
        if "nag" not in json.load(f).get("scripts", {}):
            allow()
except (OSError, ValueError):
    allow()

changed = git("diff", "--name-only", "origin/main...HEAD") + git("status", "--porcelain")
if "infra/" not in changed:
    allow()

result = subprocess.run(
    ["pnpm", "-s", "nag"], cwd=project_dir(), capture_output=True, text=True, timeout=570
)
if result.returncode == 0:
    allow()

tail = (result.stdout + result.stderr)[-4000:]
print(
    json.dumps(
        {
            "decision": "block",
            "reason": "cdk-nag failed on your infra/ changes. Fix these findings "
            "before finishing (don't suppress them without explaining why in the PR):\n\n" + tail,
        }
    )
)
allow()
