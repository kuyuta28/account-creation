# Release And Promotion Drill

## Purpose

This runbook defines the promotion path for a multi-repo platform where service repos and the root orchestration repo move independently but must agree on one runtime contract.

## Trigger

Use this runbook for:

- planned staging promotions
- planned production releases
- rollback rehearsals after major architectural changes

## Promotion Model

- Service code is promoted from each service repository.
- Root orchestration assets are promoted from the root repo only.
- A release is not valid unless service versions and root runtime docs agree on ports, route prefixes, and datastore ownership.

## Dev To Staging

1. Verify each changed service repo has a green local or CI test run.
2. Verify the root repo `docs-consistency` checks pass locally.
3. Deploy updated service images to staging.
4. Apply root orchestration changes if compose/docs/traefik assets changed.
5. Run staging smoke checks across all published endpoints.

```bash
python .github/scripts/validate_runtime_truth.py
curl http://staging-registrar.example/api/v1/health
curl http://staging-mail.example/api/health
curl http://staging-aa.example/api/health
curl http://staging-tts.example/api/health
```

## Staging Verification Gate

Do not promote to production unless all of these are true:

- service-specific smoke/unit/integration suites passed in the owning repos
- root orchestration checks passed
- PostgreSQL migrations or bootstrap changes were exercised on a local fresh database for release rehearsal and on a fresh staging database before real promotion
- desktop UI runtime config still points at the approved backend contract
- internal API consumers can still reach `registrar` on `/api/v1/internal/*`

## Production Release Gate

1. Freeze concurrent config changes.
2. Confirm the latest PostgreSQL backup completed.
3. Confirm on-call ownership for the release window.
4. Promote services in dependency order.
5. Promote root orchestration changes last if they modify shared runtime truth.

Suggested order:

1. `common` package consumers already built and published
2. `registrar`
3. `mail-service`
4. `aa-proxy`
5. `tts-proxy`
6. `web-ui`
7. root orchestration repo

## Release Evidence Template

Record this table before any staging or production promotion. Use the exact commit SHA from each owning repo or worktree. The active evidence record lives at `docs/superpowers/release-evidence/current-platform-release.md`.

| Layer | Repository | Commit SHA | Image tag or digest | Command | CI run URL | Timestamp | Result |
|-------|------------|------------|---------------------|---------|------------|-----------|--------|
| root orchestration | `account-creation` |  | n/a | `python .github/scripts/validate_runtime_truth.py` |  |  |  |
| `common` | `common` |  | n/a | `PYTHONPATH=src pytest tests -q` |  |  |  |
| `registrar` | `registrar` |  |  | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |
| `mail-service` | `mail-service` |  |  | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |
| `aa-proxy` | `aa-proxy` |  |  | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |
| `tts-proxy` | `tts-proxy` |  |  | `PYTHONPATH=src;../common/src pytest tests -q` |  |  |  |
| `web-ui` | `web-ui` |  |  | `npm test -- --run` |  |  |  |

## Rollback Triggers

Rollback immediately if any of these happen:

- health endpoint regression on any public service
- internal API contract regression between service repos
- migration/bootstrap failure on PostgreSQL
- root orchestration contract drift discovered after deploy

## Rollback Procedure

1. Stop the rollout.
2. Revert the affected service deployment or image tag in the owning service repo.
3. Revert root orchestration changes if compose/docs/routing changed in the same release.
4. If schema damage occurred, restore from backup or apply a compensating forward migration.
5. Re-run health checks before reopening traffic.

## Exit Criteria

Promotion is complete only when:

- staging or production health checks pass for every public service
- runtime truth docs still match the deployed contract
- rollback point is recorded
- operators can identify the exact service and orchestration revisions in production
