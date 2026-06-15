# GitOps Deployment Runbook

## Architecture

Root deploys released service images. Service repositories own builds and tests; root consumes image tags or digests plus release evidence.

## Staging Promotion

1. Collect fresh service CI evidence for every service.
2. Confirm database migration evidence is ready.
3. Trigger `Deploy Staging` with service image tags or digests.
4. Confirm compose validation, Flyway migration, deployment, and Traefik smoke steps pass.
5. Record workflow URL and timestamp in release evidence.

## Production Promotion

1. Promote only from a reviewed release tag.
2. Confirm staging deployment evidence exists for the same service revisions.
3. Trigger `Deploy Production` with immutable service image digests.
4. GitHub `production` environment approval must be required before the job runs.
5. Confirm migration, deploy, smoke, and observability checks pass.

## Rollback

Use roll-forward rollback by redeploying the last known-good image set through `Deploy Production`. If persistence changed, follow `docs/superpowers/runbooks/database-migrations.md` and restore procedures before redeploying application services.

## Required Evidence

- root orchestration commit SHA
- service repo commit SHA per service
- image tag or digest per service
- migration workflow URL and result
- deployment workflow URL and result
- Traefik smoke result
- timestamp
