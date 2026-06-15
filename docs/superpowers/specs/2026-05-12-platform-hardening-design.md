# Platform Hardening Design

## Goal

Close the orchestration/runtime-truth gaps that could let root documentation, service contracts, and local verification commands drift apart.

## Scope

This design covers root-owned validation and documentation for the federated account-creation workspace. It does not move service CI into the root repository, does not change service runtime ownership, and does not claim that ignored service worktrees are versioned by root Git.

## Architecture

The root repository remains an orchestration workspace. It owns Docker Compose, architecture docs, API/runtime-truth docs, runbooks, and validator scripts. Service repositories own their own executable tests and release gates.

Hardening is implemented as three layers:

1. Runtime-truth validation in `.github/scripts/validate_runtime_truth.py` for ports, health routes, API prefixes, database policy wording, release evidence shape, and documented contract artifacts.
2. Service-local smoke, unit, and contract tests in each owning service repository or local worktree.
3. Documentation that distinguishes root-owned evidence from service-owned evidence in `docs/TESTING.md`, release runbooks, and audit records.

## Contracts

The root validator enforces that documented runtime URLs match `docker-compose.yml`, that stale localhost ports are rejected, and that SQLite is not described as canonical runtime storage. It also requires explicit contract artifact documentation for common, registrar, and desktop UI tests that protect internal API usage and UI runtime configuration.

Internal API behavior is formalized in `docs/superpowers/contracts/internal-api.md`, including the `X-Internal-Key` header, documented timeout, safe retry policy, and idempotent upsert expectations.

## Test Strategy

Root verification requires:

- `python .github/scripts/validate_runtime_truth.py`
- `$env:PYTHONPATH='.github/scripts'; pytest .github/scripts/test_validate_runtime_truth.py -q`

Service verification remains local to each service repository or worktree, using the commands listed in `docs/TESTING.md`. Release evidence must record command, commit SHA, timestamp, and result for both root and service layers.

## Non-Goals

- No root-level service CI matrix that pretends ignored worktrees are checked into this repository.
- No checked-in service migration runner unless the owning service repository actually provides it.
- No broad refactor of service code beyond contract and smoke artifacts needed for hardening evidence.

## Acceptance Criteria

- Root runtime-truth validation passes.
- Validator helper tests pass.
- `docs/TESTING.md` lists the current service test floor and critical contract tests.
- Release runbook evidence table includes root and service layers with command, commit SHA, timestamp, and result columns.
- Audit documentation distinguishes completed hardening from remaining platform debt.
