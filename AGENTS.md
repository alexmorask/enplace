# Enplace: rules for droids

Enplace is a meal planner for one household, built around batch cooking: plan the week, share it, get one grocery list. It's an installable web app (PWA) on a serverless AWS backend.

This file is edited by hand only. Droids can't change it, `.factory/`, or `.github/workflows/` (a hook blocks it). If a rule here gets in the way, say so in the PR instead of working around it.

## Rules that are never broken

1. **Never touch production.** No command may use `--profile enplace-prod` or deploy anything except a `pr-*` or personal dev stack. Production deploys happen only through GitHub Actions, with Alex's approval.
2. **Never weaken a test to make it pass.** Don't edit a failing test, skip it (`.skip`, `.only`, `it.todo`), delete it, or loosen its assertions. Fix the code. If the test itself is wrong, stop and explain why in the PR.
3. **Never commit secrets.** No `.env` files, keys or tokens in the repo. Secrets live in AWS Secrets Manager.
4. **The household always comes from the token.** Never accept a household ID, member ID or role from client input. Every resolver starts with the shared membership check.
5. **Every DynamoDB key is built by `packages/core/src/keys.ts`.** Never write a `PK`/`SK` string by hand anywhere else.

## Commands

Run everything from the repo root with pnpm.

| Task | Command |
|---|---|
| Install | `pnpm install` |
| Full verification (the gate) | `pnpm verify` |
| Type-check | `pnpm typecheck` |
| Lint and format check | `pnpm lint` |
| Unit and DynamoDB Local tests | `pnpm test` |
| One package's tests | `pnpm --filter <package> test` |
| One test file | `pnpm vitest run <path>` |
| Synthesize infrastructure | `pnpm synth` |
| Infrastructure security checks (cdk-nag) | `pnpm nag` |
| Regenerate GraphQL types | `pnpm codegen` |
| Run the web app against mocked GraphQL | `pnpm --filter web dev` |
| Acceptance tests against a PR stack | `pnpm acceptance --stack pr-<number>` |

`pnpm test` needs Docker running (DynamoDB Local).

## Verification block

Before you say work is done, run:

```bash
pnpm verify
```

It runs, in order: `typecheck`, `lint`, `test`, `synth`, `nag`. All must pass.

Then paste the **complete, unedited output** into the PR description under a heading `## Verification`. Never summarize it, and never claim a check passed without its output. If a check fails and you can't fix it, paste the failing output and explain.

## Directory map

| Path | What's there |
|---|---|
| `apps/web/` | The PWA: React, Vite, TypeScript, TanStack Router and Query, Tailwind, Radix |
| `services/api/schema.graphql` | The GraphQL schema (source of truth for the API) |
| `services/api/resolvers/` | AppSync JS resolvers: straight reads and writes |
| `services/api/functions/` | Lambda resolvers: anything that checks a plan limit, calls an outside service, or computes |
| `services/workers/` | DynamoDB Streams consumers and the scheduled sweeper |
| `services/webhooks/` | Recurly webhook receiver |
| `packages/core/` | Shared code: key builders, membership check, entitlements, domain types |
| `packages/test-utils/` | DynamoDB Local setup, fixtures, seeded test users |
| `infra/` | CDK app, one stack per concern |
| `tests/integration/` | Run by CI against `pr-*` stacks |
| `tests/acceptance/` | Playwright, used by the QA droid |
| `docs/` | Architecture, data model, API, scaling plan, decisions |

Generated files: `apps/web/src/gql/` comes from `schema.graphql`. Edit the schema and run `pnpm codegen`; never edit generated files.

## How work happens

1. Work starts from a Linear issue (`ENP-<n>`). Read the whole issue, its comments, and the docs it links.
2. Branch name: `ENP-<n>-short-description`. PR title: `ENP-<n>: Short description`.
3. Start in Spec Mode. The spec lists: GraphQL changes, DynamoDB items and keys touched, files to change, and one test per acceptance criterion. After Alex approves it, post it to the Linear issue as a comment titled `Approved spec`.
4. Write tests first, from the acceptance criteria. Name each test after its criterion, e.g. `test("AC2: a used invite can't be accepted again", ...)`. Every criterion needs at least one test.
5. Build until `pnpm verify` passes. Open the PR with the verification output.
6. If a change affects `docs/data-model.md`, `docs/api.md` or `docs/architecture.md`, update them in the same PR.

## Backend conventions

- The data model is in `docs/data-model.md`. One table, `PK`/`SK`, no GSIs unless the issue says so.
- Use strongly consistent reads (`ConsistentRead: true`) for anything a user sees.
- Enforce limits (member count, credit cap, single-use invites) with **conditional writes**, never with a read followed by a write.
- Writes that must happen together use `TransactWriteItems`.
- Plan limits come from `packages/core/src/entitlements.ts`. Never hard-code a limit.
- JS resolver vs Lambda: JS for straight reads and writes. Lambda when it checks a plan limit, calls an outside service (Recurly, Bedrock, Cognito), or computes something.
- Lambdas use CDK `NodejsFunction` on Node 24. Infrastructure uses built-in CDK constructs, one stack per concern.

## Frontend conventions

- Follow the design system in `apps/web/design-system/README.md`, including its copy rules.
- Style only with Tailwind theme classes from the design tokens (`bg-cobalt`, `text-ink-soft`, `rounded-2xl`). Never write a hex value, a pixel value, or a new CSS rule.
- Build screens from the shared components in `apps/web/src/components/`. Use Radix primitives for sheets, dialogs and menus.
- Server data goes through TanStack Query hooks; routes through TanStack Router. No hand-rolled fetch state.
- Screen and board names match the Enplace: Screens artifact, as named in the issue.

## PR expectations

- `## Verification`: full `pnpm verify` output.
- `## Acceptance criteria`: each criterion with the test(s) that cover it.
- `## Notes`: anything you were unsure about or couldn't do.
