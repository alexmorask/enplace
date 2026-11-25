"""Hook 4: no secrets.

Blocks writing .env-style files and content that looks like a credential.
`.env.example` is allowed, as long as it holds no real values.
"""

import re
import sys

sys.path.insert(0, __import__("os").path.dirname(__file__))
from _common import allow, block, old_and_new_text, paths, read_event  # noqa: E402

SECRET_FILES = re.compile(r"(^|/)\.env(\.(?!example$)[\w.-]+)?$|\.(pem|key|p12|pfx)$|(^|/)credentials$")
SECRET_CONTENT = [
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "an AWS access key"),
    (re.compile(r"aws_secret_access_key\s*[=:]", re.I), "an AWS secret key"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "a private key"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b|\bgithub_pat_[A-Za-z0-9_]{30,}\b"), "a GitHub token"),
    (re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b"), "an Anthropic API key"),
    (re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}\b"), "a Slack token"),
]

REASON = "Blocked: {what}. Secrets belong in AWS Secrets Manager, never in the repo (AGENTS.md rule 3)."

event = read_event()

for path in paths(event):
    if SECRET_FILES.search(path):
        block(REASON.format(what=f"writing {path}"))

_, new = old_and_new_text(event)
for pattern, what in SECRET_CONTENT:
    if pattern.search(new):
        block(REASON.format(what=f"content looks like {what}"))

allow()
