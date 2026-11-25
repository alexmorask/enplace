"""Hook 1: no production access.

Blocks any shell command that mentions the prod AWS profile or account,
and any CDK deploy/destroy that doesn't target a pr-<n> or dev-<name> stage.
"""

import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _common import allow, block, command, read_event  # noqa: E402

event = read_event()
cmd = command(event)

if re.search(r"enplace-prod", cmd, re.I):
    block(
        "Blocked: commands may not touch production. Production deploys only happen "
        "through GitHub Actions with Alex's approval (AGENTS.md rule 1)."
    )

if re.search(r"\bcdk\s+(deploy|destroy)\b", cmd):
    stage = re.search(r"(?:-c|--context)[\s=]+stage=([\w-]+)", cmd)
    if not stage or not re.fullmatch(r"pr-\d+|dev-[a-z0-9]+", stage.group(1)):
        block(
            "Blocked: `cdk deploy`/`cdk destroy` must target a pr-<number> or dev-<name> "
            "stage, e.g. `-c stage=pr-42`. Anything else could hit a shared environment."
        )

allow()
